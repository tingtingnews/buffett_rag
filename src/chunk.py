"""
STEP 1 of the pipeline: chunking.

Turn knowledge-base markdown files into "cards" — small, self-contained pieces that the
system can retrieve one at a time. We split on markdown headers (## and ###), because the
knowledge files are deliberately written so each header block is one complete idea.

This module is pure text processing (no AI, no network), so it's easy to test too.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chunk:
    """One retrievable card."""
    text: str
    source: str                       # filename it came from
    heading: str                      # the header this block sits under
    tags: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"{self.source}::{self.heading}"


_HEADER_RE = re.compile(r"^(#{2,3})\s+(.*)$")
_TAGS_RE = re.compile(r"`tags:\s*(.*?)`")


def chunk_markdown(text: str, source: str) -> list[Chunk]:
    """Split one markdown document into Chunks on its ## and ### headers.

    Everything before the first header (front-matter, intro notes) is ignored.
    A `tags: ...` line inside a block is parsed into the chunk's tags list.
    """
    chunks: list[Chunk] = []
    current_heading: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if current_heading is None:
            return
        body = "\n".join(buffer).strip()
        if not body:
            return
        tag_match = _TAGS_RE.search(body)
        tags = (
            [t.strip() for t in tag_match.group(1).split(",") if t.strip()]
            if tag_match else []
        )
        chunks.append(
            Chunk(text=body, source=source, heading=current_heading, tags=tags)
        )

    for line in text.splitlines():
        m = _HEADER_RE.match(line)
        if m:
            flush()
            current_heading = m.group(2).strip()
            buffer = [line]
        else:
            buffer.append(line)
    flush()
    return chunks


def chunk_directory(kb_dir: str | Path) -> list[Chunk]:
    """Chunk every .md file in a knowledge-base directory."""
    kb_dir = Path(kb_dir)
    all_chunks: list[Chunk] = []
    for md_file in sorted(kb_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        all_chunks.extend(chunk_markdown(text, source=md_file.name))
    return all_chunks


if __name__ == "__main__":
    # Quick manual check: how many cards do we get?
    here = Path(__file__).resolve().parents[1]
    cs = chunk_directory(here / "data" / "knowledge_base")
    print(f"Chunked {len(cs)} cards from data/knowledge_base/")
    for c in cs[:5]:
        print(f"  - {c.id}  (tags: {', '.join(c.tags) or 'none'})")
