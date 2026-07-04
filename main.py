import time
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from orchestrator import process_user_query
from tasks import process_document_upload

app = FastAPI(
    title="Semantic Cache API",
    description="FastAPI interface for a local RAG semantic cache layer.",
)

ALLOWED_DEPARTMENTS = {"general", "engineering", "hr"}


class QueryRequest(BaseModel):
    prompt: str


@app.post("/v1/query")
async def handle_rag_query(
    payload: QueryRequest,
    x_department: str = Header(default="general", alias="X-Department"),
):
    if x_department not in ALLOWED_DEPARTMENTS:
        raise HTTPException(status_code=400, detail=f"Invalid department. Must be one of: {sorted(ALLOWED_DEPARTMENTS)}")
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        start = time.perf_counter()
        response_text = process_user_query(payload.prompt, department=x_department)
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "status": "success",
            "department_scope": x_department,
            "data": {"answer": response_text},
            "telemetry": {
                "total_processing_time_ms": round(latency_ms, 2),
                "served_by": "Cache Hit" if latency_ms < 200 else "LLM Slow Path",
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/v1/documents", status_code=202)
async def upload_document(file_name: str, department: str = "general"):
    if department not in ALLOWED_DEPARTMENTS:
        raise HTTPException(status_code=400, detail=f"Invalid department. Must be one of: {sorted(ALLOWED_DEPARTMENTS)}")
    task = process_document_upload.delay(file_name, department)
    return {
        "status": "Accepted",
        "message": "Document processing initiated in background.",
        "task_id": task.id,
    }