import time
from orchestrator import process_user_query
from cache import llm_cache

TEST_QUERIES = [
    ("What is the official corporate holiday policy for 2026?", "MISS expected"),
    ("Can I see the 2026 company holiday schedule?", "HIT expected"),
    ("Show me the calendar guidelines for office holidays in 2026", "HIT expected"),
    ("How do I connect to the office guest Wi-Fi network?", "MISS expected"),
    ("What is the password for the corporate guest wireless internet?", "HIT expected"),
    ("Steps to log into the visitor wifi system?", "HIT expected"),
]


def run_benchmark():
    print("Starting benchmark. Flushing cache...")
    llm_cache.clear()

    results = []
    for i, (query, expected) in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] {query}")
        start = time.perf_counter()
        process_user_query(query)
        latency_ms = (time.perf_counter() - start) * 1000
        results.append({
            "query": query,
            "latency": latency_ms,
            "status": "Cache Hit" if latency_ms < 200 else "Cache Miss",
        })

    print("\n" + "=" * 60)
    print("| # | Query | Latency (ms) | Status |")
    print("|---|---|---|---|")
    for idx, res in enumerate(results, 1):
        print(f"| {idx} | {res['query']} | {res['latency']:.2f} | {res['status']} |")
    print("=" * 60)


if __name__ == "__main__":
    run_benchmark()