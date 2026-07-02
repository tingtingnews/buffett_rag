"""
STEP 4 of the pipeline: retrieval.

Given a question, find the cards most related to it. This is the "R" in RAG and the
single most important step to QA — if the wrong cards come back, no clever prompt can
save the answer. evals/eval_retrieval.py measures exactly this.

    from src.retrieve import retrieve
    cards = retrieve("Should I sell when the market crashes?", k=4)
"""

from __future__ import annotations

from dataclasses import dataclass

from .ingest import COLLECTION, DB_PATH, EMBED_MODEL


@dataclass
class RetrievedCard:
    text: str
    source: str
    heading: str
    distance: float        # smaller = more similar


def retrieve(question: str, k: int = 4, db_path: str = DB_PATH) -> list[RetrievedCard]:
    """Return the top-k most relevant cards for a question."""
    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL)
    q_vector = model.encode([question]).tolist()

    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(COLLECTION)
    res = collection.query(query_embeddings=q_vector, n_results=k)

    cards: list[RetrievedCard] = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        cards.append(
            RetrievedCard(
                text=doc,
                source=meta.get("source", "?"),
                heading=meta.get("heading", "?"),
                distance=dist,
            )
        )
    return cards


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "What is a moat and why does it matter?"
    print(f"Q: {q}\n")
    for i, card in enumerate(retrieve(q), 1):
        print(f"[{i}] {card.heading}  ({card.source}, distance={card.distance:.3f})")
        print(card.text[:200].replace("\n", " ") + " ...\n")
