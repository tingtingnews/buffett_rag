"""
Download the FREE Berkshire Hathaway shareholder letters into data/letters/.

These letters are published free by Berkshire at:
    https://www.berkshirehathaway.com/letters/letters.html

Older letters are .html; newer ones are PDFs named like '2023ltr.pdf'. URL patterns have
changed over the years, so this script tries both patterns per year and saves whatever
exists. If a year fails, it's skipped (the page layout may have changed) — open the index
page above and grab any stragglers by hand.

Usage:
    python scripts/download_letters.py
    python scripts/download_letters.py --start 2010 --end 2024

Note: this fetches your OWN copy of free, public documents for personal study. The files
land in data/letters/, which is git-ignored — don't redistribute them.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import requests

BASE = "https://www.berkshirehathaway.com/letters"
OUT = Path(__file__).resolve().parents[1] / "data" / "letters"
HEADERS = {"User-Agent": "buffett-rag-personal-study/1.0"}


def candidate_urls(year: int) -> list[tuple[str, str]]:
    """(url, file_extension) candidates to try for a given year, newest pattern first."""
    return [
        (f"{BASE}/{year}ltr.pdf", "pdf"),
        (f"{BASE}/{year}.pdf", "pdf"),
        (f"{BASE}/{year}.html", "html"),
        (f"{BASE}/{year}ltr.html", "html"),
    ]


def fetch_year(year: int) -> bool:
    for url, ext in candidate_urls(year):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
        except requests.RequestException:
            continue
        if r.status_code == 200 and len(r.content) > 1000:
            dest = OUT / f"berkshire_{year}.{ext}"
            dest.write_bytes(r.content)
            print(f"  saved {dest.name}  ({len(r.content) // 1024} KB)")
            return True
    print(f"  [skip] {year}: no letter found by known URL patterns")
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1977)
    ap.add_argument("--end", type=int, default=2024)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Berkshire letters {args.start}-{args.end} into {OUT}\n")

    saved = 0
    for year in range(args.start, args.end + 1):
        print(f"{year}:")
        if fetch_year(year):
            saved += 1
        time.sleep(1)  # be polite to the server

    print(f"\nDone. Saved {saved} letters to {OUT}")
    print("Next: convert PDFs to text and add them as knowledge cards, then re-run "
          "`python -m src.ingest`.")


if __name__ == "__main__":
    main()
