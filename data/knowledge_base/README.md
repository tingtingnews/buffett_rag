# Warren Buffett Shareholder Letters (1977–2024)

All 48 annual letters from Warren Buffett to Berkshire Hathaway shareholders, converted to plain text Markdown for easy reading, searching, and use in AI/LLM workflows.

## Why this exists

The original letters live as a mix of HTML and PDF files across the Berkshire Hathaway website. This repo converts all of them to a single consistent Markdown format so you can:

- Read them without a PDF viewer
- Search across all 48 years instantly
- Feed them into an LLM or RAG pipeline
- Clone once and have the full archive locally

## Contents

48 letters spanning 1977 to 2024. Files are named by year (`1977.md` through `2024.md`).

Letters from 1977–2003 were originally HTML. Letters from 2004–2024 were originally PDF. All converted to Markdown.

## Quick start

```bash
git clone https://github.com/ReeceHarding/buffett-letters.git
cd buffett-letters
```

Each letter is a standalone Markdown file named by year. No dependencies, no preprocessing needed.

## Highlights by era

**1977–1985 — The foundation years**
Float, insurance economics, owner earnings, intrinsic value, the Mr. Market analogy, and the Ben Graham tribute.

**1986–1995 — The compounding years**
Buying Coca-Cola, the moat concept, mistakes of omission, GEICO acquisition, and the full power of float explained.

**1996–2003 — The bubble and aftermath**
The owner's manual, the dot-com bubble warning, 9/11 insurance losses, derivatives as weapons of mass destruction.

**2004–2010 — Scale and crisis**
Berkshire at full scale, pre-crisis housing warnings, buying during the 2008 panic, BNSF acquisition.

**2011–2019 — Legacy and succession**
Succession planning, 50th anniversary retrospective, index funds vs. active management, buybacks, GAAP vs. intrinsic value.

**2020–2024 — Late Buffett**
COVID and doing nothing as a strategy, American tailwind thesis, Charlie Munger tribute, record cash position.

## Generating the files yourself

A script to regenerate this collection from the original source:

```bash
pip install requests beautifulsoup4 pdfplumber brotli
python download_buffett_letters.py
```

The script (`download_buffett_letters.py`) is included in this repo. It skips already-downloaded letters so it is safe to rerun when new letters are published each year.

## Source

All letters sourced directly from [berkshirehathaway.com/letters/letters.html](https://www.berkshirehathaway.com/letters/letters.html).

The original letters are the intellectual property of Berkshire Hathaway Inc. This repo is a format conversion for educational and research use.
