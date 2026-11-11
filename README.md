# Buffett RAG — a value-investing analyst you can *test*

Ask a question about a stock. The system looks up the relevant Warren Buffett / Charlie
Munger reasoning **and** your own calibrated method, pulls the numbers, and returns a
structured verdict with a margin-of-safety score and **cited sources**.

> **This is not investment advice.** It is an analytical framework. The author is not a
> licensed financial or tax advisor.

---

## Why this repo exists (read this first)

This project does three jobs at once:

1. **A real tool** — a Buffett-style investment analyst grounded in real documents.
2. **A portfolio piece** — something concrete to show on GitHub.
3. **A QA showcase** — the reason it's hireable. Most people build a RAG that *answers*.
   Far fewer build one they can *prove is correct*. This repo treats testing and
   evaluation as first-class: deterministic financial math is unit-tested, and the
   retrieval/answer quality is measured by an eval harness. **That is the skill a
   fintech QA role is buying.**

### The one big design rule
Keep the **deterministic** part (the DCF math — same input always gives same output)
completely separate from the **probabilistic** part (the AI's answers, which vary).
- Deterministic math lives in `src/financials.py` and is covered by `tests/`.
- AI behaviour is measured in `evals/`.

This separation is itself a QA best practice and makes the whole repo easy to reason about.

---

## What a RAG is (plain version)

A RAG is a smart assistant that **looks things up before it answers** instead of
answering from fuzzy memory. "RAG" = Retrieval-Augmented Generation:

- **Retrieval** = look up the most relevant notes.
- **Augmented** = hand those notes to the AI.
- **Generation** = the AI writes the answer using them.

The pipeline, end to end:

```
                 INGESTION (done once / when you add knowledge)
  documents ──> chunk ──> embed ──> store in vector DB
  (data/)        (src/chunk.py) (src/ingest.py) (ChromaDB)

                 QUERY (runs every question)
  your question ──> embed ──> retrieve top matches ──> build prompt ──> Claude answers
                    (src/retrieve.py)                  (src/generate.py)

                 QA (wraps around everything)
  tests/  -> proves the math is right
  evals/  -> measures whether retrieval + answers are good
```

---

## Folder structure

```
buffett-rag/
├── README.md                  <- you are here
├── requirements.txt           <- libraries to install
├── .gitignore
├── data/
│   ├── README.md              <- where knowledge comes from + licensing notes
│   └── knowledge_base/
│       ├── valueos_knowledge_base.md      <- your own method (real content)
│       └── buffett_principles_sample.md   <- sample principle "cards"
├── src/
│   ├── chunk.py               <- split documents into retrievable cards
│   ├── ingest.py              <- embed cards + load into the vector DB
│   ├── retrieve.py            <- find the best cards for a question
│   ├── generate.py            <- assemble prompt + call Claude
│   └── financials.py          <- owner-earnings + DCF math (deterministic)
├── cli.py                     <- `buffett analyze / scenario / reverse / compare`
├── tests/
│   ├── test_financials.py     <- unit tests for the math (the QA core)
│   └── test_scenario_inputs.py<- the override + data-quality flag reaching the math
├── evals/
│   └── eval_retrieval.py      <- measures retrieval quality
└── scripts/
    └── download_letters.py    <- fetches the FREE Berkshire shareholder letters
```

---

## Quick start

```bash
# 1. install
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. run the tests first (no API key needed) — prove the math works
pytest -v

# 3. (optional) download the free Berkshire letters
python scripts/download_letters.py

# 4. build the knowledge base, then ask a question
export ANTHROPIC_API_KEY=sk-...   # needed only for steps that call Claude
python -m src.ingest
python -m src.generate "Is Costco a good buy right now?"
```

### Three guards on the valuation

The DCF is only as honest as what you feed it, so three things sit around it:

```bash
# 1. Reverse DCF — what growth does today's price already assume?
buffett reverse TSM                      # solves for g1; no API key, pure math
buffett reverse MSFT --price 420 --discount 10

# 2. Data-quality flag — thin or sign-flipping earnings widen the margin of safety
buffett analyze COST                     # under 5 years of history -> LOW CONFIDENCE
buffett analyze COST --min-years 4       # yfinance only supplies ~4 annual years

# 3. Mid-cycle override — for a cyclical, pass your own normalized owner earnings
buffett analyze TSM --normalized-oe 46         # $46B, used instead of the TTM recipe
buffett analyze TSM --oe-history 40,30,55,60,45  # a cycle, averaged to the mid-point
```

A **LOW CONFIDENCE** verdict is not a comment. It subtracts a fixed penalty
(`LOW_CONFIDENCE_MOS_PENALTY`, 10c) from every buy-zone threshold, so a shaky
valuation has to be 10c cheaper per $1 of intrinsic value before it reads as a buy —
and the printed price targets move down with it. It fires when the earnings history
is shorter than `--min-years`, when earnings swing between positive and negative, or
when a ticker in `CYCLICAL_TICKERS` is being valued on a single year. Supplying a
mid-cycle base clears that last one.

The reverse DCF (`implied_g1` in `src/financials.py`) holds g2, terminal growth, the
discount rate and net cash fixed and bisects for the stage-1 growth rate that makes
intrinsic value equal the price. The full report prints it per scenario, next to the
growth each scenario assumed — the question stops being "is this cheap?" and becomes
"is that growth rate believable?".

Built in **plain Python on purpose** (no LangChain). A QA role is about understanding
and verifying a system — a framework that hides the wiring works against that. Plain
modules keep every step inspectable and testable. A framework can come later if
complexity ever justifies it.

---

## Status

This is a **v1 scaffold**. The financial math and tests are real and runnable. The
embed/retrieve/generate steps are written to be filled in as you go — start by reading
`src/financials.py` and running `pytest`, since that's the part that makes you hireable.
