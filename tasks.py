import os
from celery import Celery
from cache import llm_cache

celery_app = Celery(
    "rag_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


def sliding_window_chunking(text: str, chunk_size: int = 200, overlap: int = 40) -> list:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


@celery_app.task(name="tasks.process_document_upload")
def process_document_upload(file_name: str, department: str):
    print(f"\n[WORKER] Task received: '{file_name}' [dept={department}]")

    safe_name = os.path.basename(file_name)
    file_path = os.path.join("storage", safe_name)

    if not os.path.exists(file_path):
        msg = f"File '{file_path}' not found."
        print(f"[WORKER] {msg}")
        return {"status": "failed", "reason": msg}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        chunks = sliding_window_chunking(raw_content)
        print(f"[WORKER] {len(chunks)} chunks to index.")

        for idx, chunk_text in enumerate(chunks, 1):
            llm_cache.store(
                prompt=chunk_text,
                response=chunk_text,
                ttl=3600,
                filters={"department": department},
            )
            print(f"[WORKER] Indexed chunk {idx}/{len(chunks)} [dept={department}]")

        print(f"[WORKER] Done: {file_name}")
        return {"status": "success", "chunks_indexed": len(chunks)}

    except Exception as e:
        print(f"[WORKER] Error: {e}")
        return {"status": "failed", "error": str(e)}