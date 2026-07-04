import json
import urllib.request
from redisvl.extensions.cache.llm import SemanticCache
from redisvl.utils.vectorize import CustomVectorizer


def get_ollama_embedding(text: str) -> list:
    url = "http://localhost:11434/api/embeddings"
    data = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())["embedding"]
    except Exception:
        return [0.0] * 768


vectorizer = CustomVectorizer(embed=get_ollama_embedding)

print("Connecting to Redis...")
llm_cache = SemanticCache(
    name="ollama_semantic_cache",
    redis_url="redis://localhost:6379",
    vectorizer=vectorizer,
    distance_threshold=0.30,
)
print("Ready.")