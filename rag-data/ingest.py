"""
Ingest RAG source documents into ChromaDB.
Run once before starting the backend: python rag-data/ingest.py
Requires: OPENROUTER_API_KEY in .env and ChromaDB installed.
"""
import os
import sys
import json
import httpx
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
EMBED_MODEL = "openai/text-embedding-3-small"
COLLECTION_NAME = "construction_knowledge"
CHUNK_SIZE = 500       # characters
CHUNK_OVERLAP = 50


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if len(c) > 50]


def embed(texts: list[str]) -> list[list[float]]:
    resp = httpx.post(
        "https://openrouter.ai/api/v1/embeddings",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": EMBED_MODEL, "input": texts},
        timeout=30.0,
    )
    resp.raise_for_status()
    return [item["embedding"] for item in resp.json()["data"]]


def main():
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    data_dir = Path(__file__).parent
    md_files = list(data_dir.glob("*.md"))
    print(f"Found {len(md_files)} source documents.")

    total_chunks = 0
    for md_file in md_files:
        print(f"Processing {md_file.name}...")
        text = md_file.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        print(f"  → {len(chunks)} chunks")

        # Embed in batches of 50
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            embeddings = embed(batch)
            ids = [f"{md_file.stem}_{i + j}" for j in range(len(batch))]
            collection.upsert(
                ids=ids,
                documents=batch,
                embeddings=embeddings,
                metadatas=[{"source": md_file.name, "chunk_index": i + j} for j in range(len(batch))],
            )
            total_chunks += len(batch)

    print(f"\n✅ Ingested {total_chunks} chunks into ChromaDB at {CHROMA_DB_PATH}")
    print(f"   Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    main()
