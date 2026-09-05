import os
import pickle
import re
from rank_bm25 import BM25Okapi
from app.ingestion import get_collection


BM25_STORE_PATH = "bm25_store/bm25_index.pkl"
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "for", "to",
    "of", "in", "on", "at", "by", "with", "from", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its",
    "as", "not", "no", "do", "does", "did", "will", "would", "can", "could",
    "should", "may", "might", "must", "shall", "have", "has", "had", "i",
    "you", "he", "she", "we", "they", "them", "their", "your", "my", "our",
    "his", "her", "there", "here", "when", "where", "how", "what", "which",
    "who", "whom", "why", "into", "about", "than", "so", "such", "up", "out",
    "over", "under", "again", "further", "once", "get", "got", "also"
}

def tokenize(text: str) -> list[str]:
    """Convert text into searchable terms while removing punctuation and stop words."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS]


def build_bm25_index():
    """Build a disk-backed keyword index from the chunks stored in ChromaDB."""
    collection = get_collection()
    all_data = collection.get(include=["documents", "metadatas"])

    chunk_ids = all_data["ids"]
    chunk_texts = all_data["documents"]
    chunk_metas = all_data["metadatas"]

    if not chunk_texts:
        print("[BM25] No chunks found in ChromaDB, skipping index build")
        return

    tokenized_corpus = [tokenize(t) for t in chunk_texts]
    bm25 = BM25Okapi(tokenized_corpus)

    os.makedirs(os.path.dirname(BM25_STORE_PATH), exist_ok=True)
    with open(BM25_STORE_PATH, "wb") as f:
        pickle.dump({
            "bm25": bm25,
            "ids": chunk_ids,
            "documents": chunk_texts,
            "metadatas": chunk_metas
        }, f)

    print(f"[BM25] Index built with {len(chunk_texts)} chunks")


def load_bm25_index():
    """Load the saved BM25 index, or return None before the first build."""
    if not os.path.exists(BM25_STORE_PATH):
        return None
    with open(BM25_STORE_PATH, "rb") as f:
        return pickle.load(f)


def bm25_search(query: str, top_k: int = 10, allowed_roles: list[str] = None):
    """Return the highest-scoring keyword matches after applying role filtering."""
    data = load_bm25_index()
    if data is None:
        print("[BM25] Index not found, run build_bm25_index() first")
        return []

    bm25 = data["bm25"]
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    combined = list(zip(data["ids"], data["documents"], data["metadatas"], scores))


    if allowed_roles is not None:
        combined = [
            item for item in combined
            if item[2].get("role_required", "general") in allowed_roles
        ]

    ranked = sorted(combined, key=lambda x: x[3], reverse=True)[:top_k]

    return [
        {"id": doc_id, "text": text, "score": float(score)}
        for doc_id, text, meta, score in ranked
    ]
