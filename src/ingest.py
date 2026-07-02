"""
STEPS 2 & 3 of the pipeline: embed + store.

Take the cards from chunk.py, turn each into a vector (embedding), and load them into a
ChromaDB collection on disk. Run this once, and again whenever you add knowledge.

    python -m src.ingest

Heavy libraries (sentence-transformers, chromadb) are imported inside the function so the
rest of the repo — and the tests — don't need them installed just to import this file.
"""

from __future__ import annotations

from pathlib import Path

from .chunk import chunk_directory

EMBED_MODEL = "all-MiniLM-L6-v2"      # small, fast, free local embedding model
COLLECTION = "buffett_kb"
DB_PATH = "chroma_db"                  # git-ignored; rebuilt from data/


def build_index(kb_dir: str | Path | None = None, db_path: str = DB_PATH) -> int:
    """Chunk -> embed -> store. Returns the number of cards indexed."""
    import chromadb
    from sentence_transformers import SentenceTransformer

    root = Path(__file__).resolve().parents[1]
    kb_dir = Path(kb_dir) if kb_dir else root / "data" / "knowledge_base"

    chunks = chunk_directory(kb_dir)
    if not chunks:
        raise RuntimeError(f"No cards found in {kb_dir}")

    print(f"Embedding {len(chunks)} cards with {EMBED_MODEL} ...")
    model = SentenceTransformer(EMBED_MODEL)
    vectors = model.encode([c.text for c in chunks], show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=db_path)
    # Fresh rebuild so re-running never duplicates cards.
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION)

    collection.add(
        ids=[c.id for c in chunks],
        embeddings=vectors,
        documents=[c.text for c in chunks],
        metadatas=[
            {"source": c.source, "heading": c.heading, "tags": ", ".join(c.tags)}
            for c in chunks
        ],
    )
    print(f"Stored {len(chunks)} cards in '{COLLECTION}' at ./{db_path}")
    return len(chunks)


if __name__ == "__main__":
    build_index()
