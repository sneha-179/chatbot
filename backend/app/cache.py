import os
import json
import hashlib
import time

CACHE_STORE_PATH = "cache_store/query_cache.json"
CACHE_TTL_SECONDS = 24 * 60 * 60


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().lower().split())


def _query_hash(query: str, user_role: str = "general") -> str:
    normalized = _normalize_query(query)
    combined = f"{normalized}::{user_role}"
    return hashlib.md5(combined.encode()).hexdigest()


def _load_cache() -> dict:
    if not os.path.exists(CACHE_STORE_PATH):
        return {}
    with open(CACHE_STORE_PATH, "r") as f:
        return json.load(f)


def _save_cache(cache: dict):
    os.makedirs(os.path.dirname(CACHE_STORE_PATH), exist_ok=True)
    with open(CACHE_STORE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def get_cached_answer(query: str, user_role: str = "general"):
    cache = _load_cache()
    key = _query_hash(query, user_role)

    if key not in cache:
        return None

    entry = cache[key]
    age = time.time() - entry["timestamp"]

    if age > CACHE_TTL_SECONDS:
        print(f"[Cache] Entry expired for query: {query[:50]}")
        return None

    print(f"[Cache] HIT for query: {query[:50]} (role={user_role})")
    return entry["answer"], entry["escalated"], entry.get("confidence", 0.0)


def set_cached_answer(query: str, answer: str, escalated: bool, confidence: float = 0.0, user_role: str = "general"):
    cache = _load_cache()
    key = _query_hash(query, user_role)

    cache[key] = {
        "query": query,
        "role": user_role,
        "answer": answer,
        "escalated": escalated,
        "confidence": confidence,
        "timestamp": time.time()
    }
    _save_cache(cache)
    print(f"[Cache] Saved answer for query: {query[:50]} (role={user_role})")