"""
RAG service using ChromaDB.
Ingest: python rag-data/ingest.py
Query: rag.retrieve(query, top_k=3)
"""
import os
import httpx
from pathlib import Path

CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "../chroma_db")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
COLLECTION_NAME = "construction_knowledge"
EMBED_MODEL = "openai/text-embedding-3-small"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
        return _collection
    except Exception as e:
        print(f"[RAG] ChromaDB unavailable: {e}. Returning empty results.")
        return None


def _embed(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenRouter."""
    resp = httpx.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": EMBED_MODEL, "input": texts},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return [item["embedding"] for item in data["data"]]


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Return top_k most relevant chunks for the query."""
    collection = _get_collection()
    if collection is None:
        return []
    try:
        embeddings = _embed([query])
        results = collection.query(query_embeddings=embeddings, n_results=top_k)
        chunks = []
        for i, doc in enumerate(results["documents"][0]):
            chunks.append({
                "text": doc,
                "source": results["metadatas"][0][i].get("source", "unknown"),
                "relevance": 1 - results["distances"][0][i],
            })
        return chunks
    except Exception as e:
        print(f"[RAG] Retrieve error: {e}")
        return []


def format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for injection."""
    if not chunks:
        return ""
    lines = ["[Retrieved construction knowledge]"]
    for c in chunks:
        lines.append(f"Source: {c['source']}\n{c['text']}")
        lines.append("---")
    return "\n".join(lines)
