"""
STEPS 5 & 6 of the pipeline: augment + generate.

Take the retrieved cards, build a prompt around them, and ask Claude to write a
structured Buffett-style verdict that CITES the cards it used. The model is instructed to
answer ONLY from the provided cards — that instruction is what we measure in evals
(faithfulness: did it stick to the sources, or make things up?).

    export ANTHROPIC_API_KEY=sk-...
    python -m src.generate "Is Costco a good buy right now?"
"""

from __future__ import annotations

import os
import sys

from .retrieve import retrieve

SYSTEM_PROMPT = """You are a value-investing analyst in the tradition of Warren Buffett \
and Charlie Munger. You reason using owner earnings, intrinsic value, margin of safety, \
and moat durability.

Rules:
- Answer ONLY using the numbered SOURCE CARDS provided. If the cards do not contain \
enough information to answer, say so plainly — do not invent facts or numbers.
- Cite the cards you use by their number, e.g. [1], [3].
- Be clear and concise. Prefer a reasoned range over false precision.
- End with: "This is an analytical framework, not investment advice."
"""


def build_prompt(question: str, cards) -> str:
    """Assemble the retrieved cards + question into the user message (the 'augment' step)."""
    blocks = []
    for i, c in enumerate(cards, 1):
        blocks.append(f"[{i}] (source: {c.source} — {c.heading})\n{c.text}")
    sources = "\n\n".join(blocks)
    return (
        f"SOURCE CARDS:\n\n{sources}\n\n"
        f"---\n\nQUESTION: {question}\n\n"
        f"Answer using only the source cards above, citing them by number."
    )


def answer(question: str, k: int = 5, model: str = "claude-sonnet-4-6") -> str:
    """Full query path: retrieve -> build prompt -> Claude -> text answer."""
    import anthropic

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set the ANTHROPIC_API_KEY environment variable first.")

    cards = retrieve(question, k=k)
    prompt = build_prompt(question, cards)

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


if __name__ == "__main__":
    q = " ".join(sys.argv[1:])
    if not q:
        print('Usage: python -m src.generate "your question"')
        sys.exit(1)
    print(answer(q))
