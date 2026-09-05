def rerank(hybrid_results: list[dict], top_k: int = 3) -> list[dict]:
    """Keep the highest-ranked hybrid results for the generation prompt."""
    return hybrid_results[:top_k]


def get_best_score(reranked_results: list[dict]) -> float:
    """Return zero when retrieval found no documents."""
    if not reranked_results:
        return 0.0
    return reranked_results[0]["final_score"]


def extract_texts(reranked_results: list[dict]) -> list[str]:
    """Extract document text from ranked result records."""
    return [result["text"] for result in reranked_results]
