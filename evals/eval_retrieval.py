"""
Retrieval eval harness — measures whether the RIGHT cards come back for a question.

This is the AI-side QA. Unlike tests/, retrieval quality isn't pass/fail — it's a score.
We keep a small "gold set" of questions paired with a keyword we expect to appear in a
top-k result, then compute hit@k (the fraction of questions where a good card showed up).

Run (after `python -m src.ingest`):
    python -m evals.eval_retrieval

For a real project you'd grow the gold set, track the score over time, and fail CI if it
drops. Stating that intent in an interview already puts you ahead of most candidates.
"""

from __future__ import annotations

from src.retrieve import retrieve

# Each case: a question, and a keyword we expect in at least one top-k card (case-insensitive).
GOLD_SET = [
    ("Should I sell when the market crashes?", "mr. market"),
    ("What makes a business hard for competitors to beat?", "moat"),
    ("How do I know if a stock is cheap enough to buy?", "margin of safety"),
    ("How does Buffett measure real earning power?", "owner earnings"),
    ("Is it worth just buying an index fund?", "index"),
    ("Why does a high discount rate apply to TSMC?", "geopolitic"),
]

K = 5


def evaluate(k: int = K) -> float:
    hits = 0
    print(f"Retrieval eval — hit@{k}\n" + "-" * 40)
    for question, keyword in GOLD_SET:
        cards = retrieve(question, k=k)
        blob = " ".join(c.text.lower() for c in cards)
        hit = keyword.lower() in blob
        hits += hit
        top = cards[0].heading if cards else "(none)"
        print(f"[{'PASS' if hit else 'MISS'}] {question}")
        print(f"        expected '{keyword}' | top card: {top}")
    score = hits / len(GOLD_SET)
    print("-" * 40)
    print(f"hit@{k} = {score:.0%}  ({hits}/{len(GOLD_SET)})")
    return score


if __name__ == "__main__":
    evaluate()
