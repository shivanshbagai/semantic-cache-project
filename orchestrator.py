import time
from redisvl.query.filter import Tag
from cache import llm_cache


def process_user_query(question: str, department: str = "general") -> str:
    print(f"\n[IN] '{question}' [dept={department}]")

    start = time.perf_counter()
    dept_filter = Tag("department") == department
    cache_results = llm_cache.check(prompt=question, filter_expression=dept_filter)
    elapsed = (time.perf_counter() - start) * 1000

    if cache_results:
        print(f"[FAST PATH] Cache hit. Latency: {elapsed:.2f}ms")
        return cache_results[0]["response"]

    print("[SLOW PATH] Cache miss.")
    start_llm = time.perf_counter()
    time.sleep(2.5)
    llm_response = (
        "The 2026 corporate holiday schedule includes 11 standard paid days off, "
        "including an extended winter break closure from December 24 to January 1."
    )
    print(f"[SLOW PATH] Done. Latency: {(time.perf_counter() - start_llm) * 1000:.2f}ms")

    llm_cache.store(
        prompt=question,
        response=llm_response,
        ttl=3600,
        filters={"department": department},
    )
    print(f"[CACHE] Stored with dept={department}")

    return llm_response