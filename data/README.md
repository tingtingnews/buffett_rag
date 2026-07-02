# Knowledge sources — where the "binder" comes from

The RAG can only surface what you put in here. Quality of sources caps quality of answers.

## What's already here

- **`knowledge_base/valueos_knowledge_base.md`** — your own value-investing method
  (owner-earnings DCF, canonical IVs, decision rules). This is your *edge* — content no
  one else has. It's the most valuable file in the repo.
- **`knowledge_base/buffett_principles_sample.md`** — a few principle "cards" written in
  plain paraphrase to get you started. Replace/expand with your own notes.

## What to add (and the licensing rules)

### ✅ Free and safe to use
- **Berkshire Hathaway shareholder letters (1977–present).** Published free by Berkshire
  at https://www.berkshirehathaway.com/letters/letters.html . Run
  `python scripts/download_letters.py` to fetch them into `data/letters/` (this folder is
  git-ignored so you don't commit large files).
- **Your own notes and summaries** of anything you read — always safe, and they show your
  thinking, which is exactly what an employer/reader wants to see.

### ⚠️ Copyrighted — do NOT commit to a public repo
- **Poor Charlie's Almanack**, **The Essays of Warren Buffett**, and similar books are
  copyrighted. Read them for your own study, but do not paste their text into this repo or
  push it to GitHub. Instead, write your *own* summary cards of the ideas (like
  `buffett_principles_sample.md`) — that's legal and more valuable.

## How to add a new source
1. Drop a `.md` file in `knowledge_base/`, written as self-contained `###` cards.
2. Each card should repeat its key idea so it stands alone when retrieved.
3. Keep a `tags:` line on each card for filtering.
4. Re-run `python -m src.ingest` to add it to the vector DB.
