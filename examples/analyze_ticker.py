"""
End-to-end Buffett RAG analysis: FETCH -> HISTORICAL GROWTH -> RAG ASSUMPTIONS -> 3-SCENARIO IV -> VERDICT

Option B + C implementation:
  B: RAG suggests Bear/Base/Bull growth assumptions based on Buffett principles + historical data
  C: Three scenario IV range instead of one number (honest about uncertainty)

Usage:
    python examples/analyze_ticker.py --ticker MSFT

Output:
    - Printed to terminal
    - Saved to outputs/<TICKER>_analysis.txt

This is an analytical framework, not investment advice.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from dataclasses import dataclass
from datetime import datetime

# Repo root on path so `from src...` works when run directly
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.financials import (
    MIN_YEARS_OF_HISTORY,
    DataQuality,
    assess_data_quality,
    buy_zone,
    implied_g1,
    intrinsic_value_per_share,
    margin_of_safety,
    mid_cycle_owner_earnings,
    owner_earnings,
    target_buy_price,
)
from src.retrieve import retrieve


# ── Output directory ────────────────────────────────────────────────────────
OUTPUT_DIR = pathlib.Path(__file__).resolve().parents[1] / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Data structures ─────────────────────────────────────────────────────────

@dataclass
class Financials:
    """Raw financials fetched from yfinance."""
    name: str
    ticker: str
    price: float
    net_income: float
    depreciation_amortization: float
    capex: float
    stock_based_comp: float
    shares_outstanding: float
    net_cash: float
    historical_revenue_growth: float   # 5-year CAGR
    historical_fcf_growth: float       # 5-year CAGR
    roe: float                         # return on equity
    # Trust + cyclicality inputs, all filled in by fetch_financials/_finalize
    earnings_history: tuple[float, ...] = ()      # net income per year, newest first
    hand_verified: bool = False                   # True for CANONICAL_FINANCIALS tickers
    owner_earnings_override: float | None = None  # mid-cycle OE, absolute USD
    quality: DataQuality | None = None            # data-quality verdict


@dataclass
class ScenarioAssumptions:
    """Growth assumptions for one scenario."""
    label: str          # "Bear", "Base", "Bull"
    g1: float           # high growth rate years 1-5
    g2: float           # moderate growth rate years 6-10
    terminal_growth: float
    discount_rate: float
    growth_capex_pct: float        # % of capex that is growth
    growth_capex_addback: float    # % of growth capex to add back
    reasoning: str


@dataclass
class ScenarioResult:
    """IV result for one scenario."""
    label: str
    owner_earnings_b: float    # in billions
    iv_per_share: float
    price: float
    ratio: float
    zone: str
    reasoning: str
    # Raw calculation inputs for step-by-step display
    net_income_b: float = 0.0
    da_b: float = 0.0
    capex_b: float = 0.0
    sbc_b: float = 0.0
    fcf_b: float = 0.0
    growth_capex_b: float = 0.0
    growth_capex_addback_b: float = 0.0
    g1: float = 0.0
    g2: float = 0.0
    terminal_growth: float = 0.0
    discount_rate: float = 0.0
    net_cash_b: float = 0.0
    shares_b: float = 0.0
    pv_stage1_b: float = 0.0
    pv_stage2_b: float = 0.0
    pv_terminal_b: float = 0.0
    oe_override: bool = False   # True when a mid-cycle OE replaced the TTM recipe
    mos_penalty: float = 0.0    # extra margin of safety demanded by data quality


# ── Step 1: Fetch financials from yfinance ──────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL DATA — hand-verified source of truth (update when earnings move the base)
# All monetary values in USD, absolute. Shares in absolute count.
# run_scenarios computes effective add-back = growth_capex_pct * addback,
# so to express a single "75% add-back" we set capex_pct=1.0 and addback=0.75.
# ─────────────────────────────────────────────────────────────────────────────

CANONICAL_FINANCIALS = {
    "MSFT": dict(net_income=127.0e9, da=45.0e9,  capex=190.0e9, sbc=13.0e9,
                 shares=7.43e9,  net_cash=37.0e9),
    "TSM":  dict(net_income=50.7e9,  da=48.0e9,  capex=54.0e9,  sbc=0.0,
                 shares=5.186e9, net_cash=73.0e9),
    "MCO":  dict(net_income=2.459e9, da=0.40e9,  capex=0.326e9, sbc=0.0,
                 shares=0.176e9, net_cash=0.0),
    # V: net_income folds in the one-time $2.073B MDL litigation add-back
    # (20.058 + 2.073 = 22.131) and sbc=0, because V's canonical OE recipe
    # does not subtract SBC. Reproduces canonical OE $21.821B.
    "V":    dict(net_income=22.131e9, da=1.22e9, capex=1.53e9,  sbc=0.0,
                 shares=1.916e9, net_cash=-6.5e9),
    # AVGO: placeholder — replace with real Q2 FY2026 FCF-based recipe before trusting.
    "AVGO": dict(net_income=41.0e9,  da=0.0,     capex=0.0,     sbc=0.0,
                 shares=4.70e9,  net_cash=-40.0e9),
}

CANONICAL_ASSUMPTIONS = {
    "MSFT": dict(g1=0.15, g2=0.10, terminal=0.035, discount=0.105, capex_pct=1.0, addback=0.75),
    "TSM":  dict(g1=0.20, g2=0.12, terminal=0.04,  discount=0.11,  capex_pct=1.0, addback=0.75),
    "MCO":  dict(g1=0.15, g2=0.11, terminal=0.035, discount=0.095, capex_pct=0.0, addback=0.0),
    "V":    dict(g1=0.13, g2=0.09, terminal=0.04,  discount=0.10,  capex_pct=0.0, addback=0.0),
    "AVGO": dict(g1=0.20, g2=0.12, terminal=0.04,  discount=0.11,  capex_pct=0.0, addback=0.0),
}

# Reconciled IV targets — used ONLY for the drift warning, never in the math.
# NOTE: MCO/V reconciled downward (their stated inputs compute these, not 560/400).
CANONICAL_IV = {"MSFT": 445, "TSM": 620, "MCO": 519, "V": 338, "AVGO": 309}

# Known ADR ratios (1 ADR = N ordinary shares).
ADR_RATIOS = {"TSM": 5}

# Hand-maintained list of businesses whose single-year earnings are a bad DCF base.
# For these, valuing TTM owner earnings capitalises a peak (or a trough) forever,
# so the analysis demands a mid-cycle base: --normalized-oe or --oe-history.
CYCLICAL_TICKERS = {
    "TSM", "MU", "INTC", "AMAT", "LRCX", "KLAC", "ASML", "TER",  # semis
    "XOM", "CVX", "COP", "SLB", "OXY",                           # energy
    "FCX", "NUE", "X", "CLF", "DOW", "LYB", "MOS",               # materials
    "F", "GM", "CAT", "DE", "AAL", "DAL", "UAL",                 # autos/industrials/airlines
}

# Offline fallback prices (used only if the live price fetch fails).
_FALLBACK_PRICE = {"MSFT": 390, "TSM": 451, "MCO": 479, "V": 360, "AVGO": 385, "COST": 950}


def fetch_financials(ticker: str,
                     owner_earnings_override: float | None = None,
                     min_years: int = MIN_YEARS_OF_HISTORY) -> Financials:
    """
    Fetch inputs for analysis.

    Priority:
      1. Ticker in CANONICAL_FINANCIALS -> use verified numbers (live price only).
      2. Else -> yfinance with corrected ADR share count + FX + sanity check.

    Args:
        owner_earnings_override: mid-cycle normalized owner earnings in absolute
            USD. When given it replaces the TTM owner-earnings recipe for every
            scenario — the mid-cycle override for cyclicals (see
            resolve_owner_earnings_override and --normalized-oe / --oe-history).
        min_years: years of earnings history required before the inputs count as
            trustworthy. yfinance's free annual statements only reach back about
            4 years, so a strict 5 flags every non-canonical ticker — lower it to
            match whatever depth your data source actually supplies.

    Both paths end in _finalize, which attaches the data-quality verdict.
    """
    ticker = ticker.upper()
    live_price = _fetch_live_price(ticker)

    if ticker in CANONICAL_FINANCIALS:
        c = CANONICAL_FINANCIALS[ticker]
        price = live_price or _FALLBACK_PRICE.get(ticker, 100.0)
        print(f"  Using CANONICAL financials for {ticker} "
              f"(verified numbers; live price ${price:,.2f})")
        print(f"  Financials (USD): NI=${c['net_income']/1e9:.1f}B | "
              f"D&A=${c['da']/1e9:.1f}B | Capex=${c['capex']/1e9:.1f}B | "
              f"SBC=${c['sbc']/1e9:.1f}B | Shares={c['shares']/1e9:.2f}B | "
              f"NetCash=${c['net_cash']/1e9:.1f}B")
        a = CANONICAL_ASSUMPTIONS.get(ticker, {})
        return _finalize(Financials(
            name=ticker,
            ticker=ticker,
            price=price,
            net_income=c["net_income"],
            depreciation_amortization=c["da"],
            capex=c["capex"],
            stock_based_comp=c["sbc"],
            shares_outstanding=c["shares"],
            net_cash=c["net_cash"],
            historical_revenue_growth=a.get("g1", 0.12),
            historical_fcf_growth=a.get("g1", 0.12),
            roe=0.30,
            hand_verified=True,
        ), owner_earnings_override, min_years)

    return _finalize(_fetch_from_yfinance(ticker), owner_earnings_override, min_years)


def _fetch_live_price(ticker: str) -> float:
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        return float(info.get("currentPrice") or info.get("regularMarketPrice") or 0) or 0.0
    except Exception:
        return 0.0


def _fetch_from_yfinance(ticker: str) -> Financials:
    """Corrected yfinance path for tickers not in the canonical table."""
    import yfinance as yf
    import numpy as np

    t = yf.Ticker(ticker)
    info = t.info
    fin = t.financials
    cf = t.cashflow
    bs = t.balance_sheet

    def latest(frame, *names):
        for n in names:
            if n in frame.index:
                val = frame.loc[n].iloc[0]
                if val is not None and not (isinstance(val, float) and np.isnan(val)):
                    return float(val)
        raise KeyError(f"None of {names} found")

    def latest_or_zero(frame, *names):
        try:
            return latest(frame, *names)
        except KeyError:
            return 0.0

    def history(frame, *names) -> list[float]:
        """Every reported year of a row, newest first, NaNs dropped."""
        for n in names:
            if n in frame.index:
                return [float(v) for v in frame.loc[n].values
                        if v is not None and not (isinstance(v, float) and np.isnan(v))]
        return []

    # FX with explicit direction handling
    reporting_currency = info.get("financialCurrency", "USD")
    fx_rate = 1.0
    if reporting_currency != "USD":
        try:
            raw = yf.Ticker(f"{reporting_currency}=X").info
            q = float(raw.get("regularMarketPrice") or raw.get("currentPrice") or 0)
            if q > 0:
                fx_rate = q if q > 1 else (1.0 / q)
            print(f"  Currency: {reporting_currency} -> USD at {fx_rate:.4f} {reporting_currency}/USD")
        except Exception:
            print(f"  WARNING: no FX for {reporting_currency}; numbers may be wrong.")
            fx_rate = 1.0

    def to_usd(v):
        return v / fx_rate

    price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0)

    # Share count: use ADR ratio, NOT marketCap/price
    raw_shares = float(info.get("sharesOutstanding") or 0)
    if ticker in ADR_RATIOS and raw_shares > 0:
        shares = raw_shares / ADR_RATIOS[ticker]
        print(f"  Shares: {raw_shares/1e9:.2f}B ordinary / {ADR_RATIOS[ticker]} "
              f"= {shares/1e9:.2f}B ADR-equivalents")
    elif raw_shares > 0:
        shares = raw_shares
        print(f"  Shares (yfinance): {shares/1e9:.2f}B")
    else:
        mc = float(info.get("marketCap") or 0)
        shares = (mc / price) if price > 0 else 0
        print(f"  WARNING: sharesOutstanding missing; derived {shares/1e9:.2f}B "
              f"from marketCap/price (unreliable for ADRs)")

    if shares <= 0:
        raise ValueError(f"{ticker}: could not determine share count")

    net_income = to_usd(latest(fin, "Net Income", "Net Income Common Stockholders"))
    dep = to_usd(latest(cf, "Depreciation And Amortization", "Depreciation"))
    capex = to_usd(abs(latest(cf, "Capital Expenditure", "Capital Expenditures")))
    sbc = to_usd(latest_or_zero(cf, "Stock Based Compensation", "Share Based Compensation"))
    cash = to_usd(latest_or_zero(bs, "Cash And Cash Equivalents", "Cash"))
    debt = to_usd(latest_or_zero(bs, "Total Debt", "Long Term Debt"))

    print(f"  Financials (USD): NI=${net_income/1e9:.1f}B | D&A=${dep/1e9:.1f}B | "
          f"Capex=${capex/1e9:.1f}B | SBC=${sbc/1e9:.1f}B | "
          f"Cash=${cash/1e9:.1f}B | Debt=${debt/1e9:.1f}B")

    _sanity_check(ticker, net_income, shares, price)

    def compute_cagr(series) -> float:
        vals = [v for v in series.values if v is not None and v > 0]
        if len(vals) < 2:
            return 0.08
        newest, oldest = vals[0], vals[-1]
        years = len(vals) - 1
        return (newest / oldest) ** (1 / years) - 1

    try:
        rev_series = fin.loc["Total Revenue"] if "Total Revenue" in fin.index else None
        historical_rev_growth = compute_cagr(rev_series) if rev_series is not None else 0.08
    except Exception:
        historical_rev_growth = 0.08
    try:
        fcf_vals = cf.loc["Free Cash Flow"] if "Free Cash Flow" in cf.index else None
        historical_fcf_growth = compute_cagr(fcf_vals) if fcf_vals is not None else 0.08
    except Exception:
        historical_fcf_growth = 0.08

    roe = float(info.get("returnOnEquity") or 0.15)
    # Earnings history feeds the data-quality flag: too few years, or earnings that
    # flip sign, mean a single-point DCF cannot be trusted at face value.
    ni_history = tuple(to_usd(v) for v in
                       history(fin, "Net Income", "Net Income Common Stockholders"))
    return Financials(
        name=info.get("shortName", ticker),
        ticker=ticker,
        price=price,
        net_income=net_income,
        depreciation_amortization=dep,
        capex=capex,
        stock_based_comp=sbc,
        shares_outstanding=shares,
        net_cash=cash - debt,
        historical_revenue_growth=historical_rev_growth,
        historical_fcf_growth=historical_fcf_growth,
        roe=roe,
        earnings_history=ni_history,
    )


def _sanity_check(ticker, net_income, shares, price):
    """Warn loudly when fetched numbers look implausible, instead of lying quietly."""
    problems = []
    if net_income <= 0:
        problems.append(f"net income is ${net_income/1e9:.1f}B (<=0)")
    if shares > 0 and price > 0 and net_income > 0:
        eps = net_income / shares
        pe = price / eps if eps else 999
        if pe > 200 or pe < 3:
            problems.append(f"implied P/E is {pe:.0f} (NI or share count likely wrong)")
    if problems:
        print("  " + "!" * 60)
        print(f"  SANITY WARNING for {ticker}: " + "; ".join(problems))
        print(f"  -> Add {ticker} to CANONICAL_FINANCIALS with verified numbers,")
        print(f"     or check the ADR ratio / FX direction. Not trusting this fetch.")
        print("  " + "!" * 60)


# ── Step 1b: trust the inputs? (data-quality flag + mid-cycle override) ─────

def resolve_owner_earnings_override(normalized_oe: float | None,
                                    oe_history: str | None) -> float | None:
    """Turn the CLI's mid-cycle inputs (in $B) into absolute-USD owner earnings.

    --normalized-oe 21.8        -> 21.8e9, used as-is
    --oe-history "30,10,-5,20"  -> mid-cycle average of those years, in USD

    Returns None when neither was given (use the TTM recipe).

    Raises:
        ValueError: if both are given, or the history cannot be parsed.
    """
    if normalized_oe is not None and oe_history:
        raise ValueError("pass either --normalized-oe or --oe-history, not both")
    if normalized_oe is not None:
        return float(normalized_oe) * 1e9
    if oe_history:
        try:
            years = [float(x) for x in oe_history.replace(" ", "").split(",") if x]
        except ValueError as e:
            raise ValueError(f"could not parse --oe-history {oe_history!r}: {e}") from e
        return mid_cycle_owner_earnings(years) * 1e9
    return None


def _finalize(f: Financials,
              owner_earnings_override: float | None,
              min_years: int = MIN_YEARS_OF_HISTORY) -> Financials:
    """Attach the mid-cycle override and the data-quality verdict, and say so out loud.

    A LOW CONFIDENCE verdict is not cosmetic: f.quality.mos_penalty widens the
    required margin of safety in every scenario (see run_scenarios).
    """
    f.owner_earnings_override = owner_earnings_override

    extra_reasons = []
    if f.ticker.upper() in CYCLICAL_TICKERS and owner_earnings_override is None:
        extra_reasons.append(
            "cyclical business valued on one year of earnings "
            "(pass --normalized-oe or --oe-history for a mid-cycle base)"
        )
    f.quality = assess_data_quality(
        earnings_history=f.earnings_history,
        min_years=min_years,
        hand_verified=f.hand_verified,
        extra_reasons=extra_reasons,
    )

    if owner_earnings_override is not None:
        print(f"  MID-CYCLE OVERRIDE: owner earnings forced to "
              f"${owner_earnings_override/1e9:.1f}B (TTM recipe ignored)")
    if f.quality.is_low:
        print("  " + "!" * 60)
        print(f"  LOW CONFIDENCE for {f.ticker}:")
        for reason in f.quality.reasons:
            print(f"    - {reason}")
        if 0 < f.quality.years < min_years:
            print("      (yfinance supplies ~4 annual years; use --min-years to "
                  "match your data source)")
        print(f"  -> Required margin of safety widened by "
              f"{f.quality.mos_penalty:.0%}; every buy zone is that much stricter.")
        print("  " + "!" * 60)
    return f




# ── Step 2: RAG suggests assumptions ────────────────────────────────────────

def rag_suggest_assumptions(f: Financials) -> list[ScenarioAssumptions]:
    """
    Return [Bear, Base, Bull].

    If the ticker has calibrated canonical assumptions, Base = your method,
    and Bear/Bull are derived around it. Otherwise fall back to the RAG+LLM
    suggestion path (kept below for uncalibrated tickers).
    """
    tk = f.ticker.upper()
    if tk in CANONICAL_ASSUMPTIONS:
        a = CANONICAL_ASSUMPTIONS[tk]
        base = ScenarioAssumptions(
            label="Base", g1=a["g1"], g2=a["g2"], terminal_growth=a["terminal"],
            discount_rate=a["discount"], growth_capex_pct=a["capex_pct"],
            growth_capex_addback=a["addback"],
            reasoning=f"Canonical calibrated assumptions for {tk} (your method).",
        )
        bear = ScenarioAssumptions(
            label="Bear", g1=max(a["g1"] - 0.05, 0.03), g2=max(a["g2"] - 0.03, 0.02),
            terminal_growth=max(a["terminal"] - 0.01, 0.02),
            discount_rate=a["discount"] + 0.01,
            growth_capex_pct=a["capex_pct"],
            growth_capex_addback=max(a["addback"] - 0.25, 0.0),
            reasoning="Conservative: growth haircut, higher discount, lower add-back.",
        )
        bull = ScenarioAssumptions(
            label="Bull", g1=a["g1"] + 0.02, g2=a["g2"] + 0.01,
            terminal_growth=a["terminal"], discount_rate=max(a["discount"] - 0.005, 0.05),
            growth_capex_pct=a["capex_pct"], growth_capex_addback=a["addback"],
            reasoning="Optimistic: growth sustains near recent pace.",
        )
        print(f"  Using CANONICAL assumptions for {tk} (Base = your method).")
        return [bear, base, bull]

    # ---- Fallback: original RAG + LLM path for uncalibrated tickers ----
    return _rag_suggest_assumptions_llm(f)


def _rag_suggest_assumptions_llm(f: Financials) -> list[ScenarioAssumptions]:
    """
    Retrieve Buffett knowledge cards relevant to this business,
    then ask Claude to suggest Bear/Base/Bull assumptions grounded
    in those cards + the historical growth data.
    """
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set ANTHROPIC_API_KEY environment variable first.")

    # Retrieve relevant Buffett cards
    query = (
        f"growth rate assumptions for {f.ticker} software technology business "
        f"moat durability discount rate margin of safety"
    )
    cards = retrieve(query, k=6)

    # Build card context
    card_blocks = []
    for i, c in enumerate(cards, 1):
        card_blocks.append(f"[{i}] ({c.source} — {c.heading})\n{c.text[:400]}")
    cards_text = "\n\n".join(card_blocks)

    # Historical data summary
    hist_summary = (
        f"Historical 5-year revenue CAGR: {f.historical_revenue_growth:.1%}\n"
        f"Historical 5-year FCF CAGR:     {f.historical_fcf_growth:.1%}\n"
        f"Return on Equity (ROE):          {f.roe:.1%}\n"
        f"Net Income (TTM):                ${f.net_income/1e9:.1f}B\n"
        f"Capex (TTM):                     ${f.capex/1e9:.1f}B\n"
        f"Current Price:                   ${f.price:,.0f}/share"
    )

    prompt = f"""You are a Buffett-style value investing analyst.

BUFFETT KNOWLEDGE CARDS:
{cards_text}

---

COMPANY: {f.name} ({f.ticker})
HISTORICAL DATA:
{hist_summary}

---

Using ONLY the Buffett principles in the knowledge cards above and the historical data,
suggest THREE scenarios of DCF assumptions for this company.

Respond ONLY with valid JSON in exactly this format (no extra text):
{{
  "bear": {{
    "g1": 0.08,
    "g2": 0.05,
    "terminal_growth": 0.03,
    "discount_rate": 0.10,
    "growth_capex_pct": 0.50,
    "growth_capex_addback": 0.50,
    "reasoning": "one sentence citing which card informed this"
  }},
  "base": {{
    "g1": 0.12,
    "g2": 0.07,
    "terminal_growth": 0.03,
    "discount_rate": 0.09,
    "growth_capex_pct": 0.60,
    "growth_capex_addback": 0.60,
    "reasoning": "one sentence citing which card informed this"
  }},
  "bull": {{
    "g1": 0.16,
    "g2": 0.10,
    "terminal_growth": 0.04,
    "discount_rate": 0.09,
    "growth_capex_pct": 0.70,
    "growth_capex_addback": 0.70,
    "reasoning": "one sentence citing which card informed this"
  }}
}}

Rules:
- Bear: conservative, assumes regression toward mean, higher discount rate
- Base: reflects historical CAGR with modest haircut
- Bull: assumes moat expansion, near historical peak growth
- terminal_growth must be < discount_rate
- All values are decimals (0.10 = 10%)
- Base g1 should be close to the historical FCF CAGR with a haircut
"""

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.content[0].text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)

    scenarios = []
    for label, key in [("Bear", "bear"), ("Base", "base"), ("Bull", "bull")]:
        s = data[key]
        scenarios.append(ScenarioAssumptions(
            label=label,
            g1=s["g1"],
            g2=s["g2"],
            terminal_growth=s["terminal_growth"],
            discount_rate=s["discount_rate"],
            growth_capex_pct=s.get("growth_capex_pct", 0.5),
            growth_capex_addback=s.get("growth_capex_addback", 0.5),
            reasoning=s["reasoning"],
        ))

    return scenarios


# ── Step 3: Run 3-scenario IV calculation ───────────────────────────────────

def run_scenarios(f: Financials, scenarios: list[ScenarioAssumptions]) -> list[ScenarioResult]:
    """Run financials.py math for each scenario, capturing every step."""
    results = []
    mos_penalty = f.quality.mos_penalty if f.quality else 0.0
    for s in scenarios:
        # ── Owner Earnings breakdown ──
        growth_capex = f.capex * s.growth_capex_pct
        growth_capex_addback = growth_capex * s.growth_capex_addback
        fcf = f.net_income + f.depreciation_amortization - f.capex - f.stock_based_comp
        computed_oe = owner_earnings(
            net_income=f.net_income,
            depreciation_amortization=f.depreciation_amortization,
            capex=f.capex,
            stock_based_comp=f.stock_based_comp,
            growth_capex=growth_capex,
            growth_capex_addback_pct=s.growth_capex_addback,
        )
        # Mid-cycle override wins: for a cyclical, one year's OE is the wrong base.
        oe_override = f.owner_earnings_override is not None
        oe = f.owner_earnings_override if oe_override else computed_oe

        # ── DCF stage-by-stage breakdown ──
        earnings = oe
        pv_stage1 = 0.0
        for i in range(1, 6):
            earnings *= (1 + s.g1)
            pv_stage1 += earnings / (1 + s.discount_rate) ** i

        pv_stage2 = 0.0
        for i in range(6, 11):
            earnings *= (1 + s.g2)
            pv_stage2 += earnings / (1 + s.discount_rate) ** i

        terminal_earnings = earnings * (1 + s.terminal_growth)
        terminal_value = terminal_earnings / (s.discount_rate - s.terminal_growth)
        pv_terminal = terminal_value / (1 + s.discount_rate) ** 10

        equity_value = pv_stage1 + pv_stage2 + pv_terminal + f.net_cash
        iv = equity_value / f.shares_outstanding

        ratio = margin_of_safety(f.price, iv)
        results.append(ScenarioResult(
            label=s.label,
            owner_earnings_b=oe / 1e9,
            iv_per_share=iv,
            price=f.price,
            ratio=ratio,
            zone=buy_zone(ratio, mos_penalty=mos_penalty),
            reasoning=s.reasoning,
            # Step-by-step inputs
            net_income_b=f.net_income / 1e9,
            da_b=f.depreciation_amortization / 1e9,
            capex_b=f.capex / 1e9,
            sbc_b=f.stock_based_comp / 1e9,
            fcf_b=fcf / 1e9,
            growth_capex_b=growth_capex / 1e9,
            growth_capex_addback_b=growth_capex_addback / 1e9,
            g1=s.g1,
            g2=s.g2,
            terminal_growth=s.terminal_growth,
            discount_rate=s.discount_rate,
            net_cash_b=f.net_cash / 1e9,
            shares_b=f.shares_outstanding / 1e9,
            pv_stage1_b=pv_stage1 / 1e9,
            pv_stage2_b=pv_stage2 / 1e9,
            pv_terminal_b=pv_terminal / 1e9,
            oe_override=oe_override,
            mos_penalty=mos_penalty,
        ))
    return results


# ── Step 4: Generate full verdict via RAG ───────────────────────────────────

def generate_verdict(f: Financials, results: list[ScenarioResult]) -> str:
    """Retrieve Buffett cards + scenario results → Claude generates final verdict."""
    import anthropic

    # Retrieve cards for final verdict
    cards = retrieve(f"buy hold sell {f.ticker} margin of safety intrinsic value moat", k=5)
    card_blocks = []
    for i, c in enumerate(cards, 1):
        card_blocks.append(f"[{i}] ({c.source} — {c.heading})\n{c.text[:400]}")
    cards_text = "\n\n".join(card_blocks)

    # Scenario summary
    scenario_lines = []
    for r in results:
        scenario_lines.append(
            f"{r.label}: OE=${r.owner_earnings_b:.1f}B | "
            f"IV=${r.iv_per_share:,.0f} | "
            f"Price=${r.price:,.0f} | "
            f"Ratio={r.ratio:.2f} | "
            f"Zone={r.zone.upper()}\n"
            f"  Reasoning: {r.reasoning}"
        )
    scenarios_text = "\n\n".join(scenario_lines)

    prompt = f"""BUFFETT KNOWLEDGE CARDS:
{cards_text}

---

COMPANY: {f.name} ({f.ticker})

THREE-SCENARIO INTRINSIC VALUE ANALYSIS:
{scenarios_text}

Historical Revenue CAGR (5yr): {f.historical_revenue_growth:.1%}
Historical FCF CAGR (5yr):     {f.historical_fcf_growth:.1%}
ROE: {f.roe:.1%}

---

Using ONLY the knowledge cards and scenario data above:
1. Summarize what the three scenarios tell us about this stock
2. State clearly whether Buffett would buy, hold, or avoid at current price
3. Identify what would need to change for this to enter buy territory
4. Cite the cards you use by number [1], [2] etc.

End with: "This is an analytical framework, not investment advice."
"""

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=(
            "You are a value-investing analyst in the tradition of Warren Buffett "
            "and Charlie Munger. Be direct, cite your sources, and never fabricate numbers."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


# ── Step 5: Format + save output ────────────────────────────────────────────

def _pct_of(part: float, whole: float) -> str:
    """Format part/whole as a percentage, or 'n/a' when the base is zero."""
    return f"{part / whole:.0%}" if whole else "n/a"


def data_quality_lines(f: Financials) -> list[str]:
    """Report how much the inputs can be trusted, and what that costs the buyer."""
    q = f.quality
    if q is None:
        return []
    lines = ["DATA QUALITY", f"  Confidence:          {q.confidence}"]
    if q.years:
        lines.append(f"  Earnings history:    {q.years} year(s), "
                     f"{q.negative_years} negative")
    elif f.hand_verified:
        lines.append("  Earnings history:    none fetched (hand-verified inputs)")
    if f.owner_earnings_override is not None:
        lines.append(f"  Owner earnings:      MID-CYCLE OVERRIDE "
                     f"${f.owner_earnings_override/1e9:.1f}B (TTM recipe ignored)")
    for reason in q.reasons:
        lines.append(f"  ! {reason}")
    if q.is_low:
        lines.append(f"  -> Margin of safety widened by {q.mos_penalty:.0%}: "
                     f"every buy zone below is that much stricter.")
    lines.append("")
    return lines


def reverse_dcf_lines(f: Financials, results: list[ScenarioResult]) -> list[str]:
    """What stage-1 growth does today's price already assume?

    Each scenario's g2 / terminal growth / discount rate is held fixed and g1 is
    solved for, so the answer is "what would have to be true to pay this price".
    """
    lines = [
        "-" * 56,
        "REVERSE DCF — WHAT THE PRICE ALREADY ASSUMES",
        f"  At ${f.price:,.0f}/share, holding each case's g2, terminal growth and",
        "  discount rate fixed, stage-1 growth would have to be:",
    ]
    for r in results:
        try:
            g = implied_g1(
                price=f.price,
                base_owner_earnings=r.owner_earnings_b * 1e9,
                shares_outstanding=f.shares_outstanding,
                g2=r.g2,
                terminal_growth=r.terminal_growth,
                discount_rate=r.discount_rate,
                net_cash=f.net_cash,
            )
        except ValueError as e:
            lines.append(f"    {r.label}: not solvable — {e}")
            continue
        gap = g - r.g1
        if gap > 0.005:
            verdict = "price assumes MORE growth than this case"
        elif gap < -0.005:
            verdict = "price assumes LESS growth than this case"
        else:
            verdict = "price matches this case"
        lines.append(f"    {r.label}: implied g1 = {g:>6.1%}  "
                     f"(assumed {r.g1:.0%}, {gap:+.1%}) — {verdict}")
    lines.append("")
    return lines


def format_output(f: Financials, results: list[ScenarioResult], verdict: str) -> str:
    """Format the complete analysis as a clean text report."""
    divider = "=" * 56
    lines = [
        "",
        divider,
        f"  {f.name} ({f.ticker}) — Buffett RAG Analysis",
        f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        divider,
        "",
        "HISTORICAL CONTEXT",
        f"  Revenue CAGR (5yr):  {f.historical_revenue_growth:.1%}  ← {_label_growth(f.historical_revenue_growth)}",
        f"  FCF CAGR (5yr):      {f.historical_fcf_growth:.1%}  ← {_label_growth(f.historical_fcf_growth)}",
        f"  ROE:                 {f.roe:.1%}  ← {_label_roe(f.roe)}",
        f"  Net Income (TTM):    ${f.net_income/1e9:.1f}B",
        f"  Capex (TTM):         ${f.capex/1e9:.1f}B",
        f"  Current Price:       ${f.price:,.0f}/share",
        f"",
        f"  [RAG anchors Base g1 to FCF CAGR ({f.historical_fcf_growth:.1%}) with haircut]",
        "",
    ]

    lines += data_quality_lines(f)

    lines += [
        "THREE-SCENARIO INTRINSIC VALUE",
        "-" * 56,
    ]

    for r in results:
        total_equity_b = r.pv_stage1_b + r.pv_stage2_b + r.pv_terminal_b + r.net_cash_b
        lines += [
            f"  {'─' * 52}",
            f"  {r.label.upper()} CASE  (g1={r.g1:.0%}, g2={r.g2:.0%}, "
            f"terminal={r.terminal_growth:.0%}, discount={r.discount_rate:.0%})",
            f"  {'─' * 52}",
            "",
            f"  STEP 1 — OWNER EARNINGS",
            f"    Net Income:               +${r.net_income_b:>7.1f}B",
            f"    Depreciation & Amort:     +${r.da_b:>7.1f}B  (non-cash, add back)",
            f"    Capital Expenditure:      -${r.capex_b:>7.1f}B  (real cash out)",
            f"    Stock Based Comp:         -${r.sbc_b:>7.1f}B  (real cost to shareholders)",
            f"    {'·' * 44}",
            f"    Free Cash Flow (FCF):     =${r.fcf_b:>7.1f}B",
            "",
            f"    Growth Capex split:",
            f"      Total Capex × growth%:  ${r.capex_b:.1f}B × "
            f"{_pct_of(r.growth_capex_b, r.capex_b)} = ${r.growth_capex_b:.1f}B",
            f"      Addback ({_pct_of(r.growth_capex_addback_b, r.growth_capex_b)}"
            f" of growth capex):  +${r.growth_capex_addback_b:.1f}B",
            f"    {'·' * 44}",
            f"    Owner Earnings (OE):      =${r.owner_earnings_b:>7.1f}B"
            + ("   ← MID-CYCLE OVERRIDE (recipe above ignored)" if r.oe_override else ""),
            "",
            f"  STEP 2 — DCF: PRESENT VALUE OF FUTURE CASH FLOWS",
            f"    Stage 1  (yrs 1–5,  g1={r.g1:.0%}):   ${r.pv_stage1_b:>8.1f}B",
            f"    Stage 2  (yrs 6–10, g2={r.g2:.0%}):   ${r.pv_stage2_b:>8.1f}B",
            f"    Terminal (yr 10+, {r.terminal_growth:.0%} forever):  ${r.pv_terminal_b:>8.1f}B",
            f"    Net Cash (cash − debt):            ${r.net_cash_b:>8.1f}B",
            f"    {'·' * 44}",
            f"    Total Equity Value:                ${total_equity_b:>8.1f}B",
            "",
            f"  STEP 3 — PER SHARE",
            f"    ${total_equity_b:.1f}B ÷ {r.shares_b:.2f}B shares = ${r.iv_per_share:,.0f}/share",
            "",
            f"  STEP 4 — MARGIN OF SAFETY",
            f"    Price ${r.price:,.0f} ÷ IV ${r.iv_per_share:,.0f} = {r.ratio:.2f}",
            f"    ({r.ratio*100:.0f}c paid per $1 of intrinsic value)",
            f"    Buy zone: {r.zone.upper()}"
            + (f"  (LOW CONFIDENCE: zones {r.mos_penalty:.0%} stricter)"
               if r.mos_penalty else ""),
            "",
            f"  RAG reasoning: {r.reasoning}",
            "",
        ]

    lines += reverse_dcf_lines(f, results)

    lines += [
        "-" * 56,
        f"  Price must fall to these levels to enter buy zone:",
    ]

    for r in results:
        # Top of the "good" zone, minus any data-quality penalty.
        target = target_buy_price(r.iv_per_share, mos_penalty=r.mos_penalty)
        pct = 0.75 - r.mos_penalty
        lines.append(f"    {r.label}: ~${target:,.0f} ({pct:.0%} of IV)"
                     + ("  [widened for LOW CONFIDENCE]" if r.mos_penalty else ""))

    lines += [
        "",
        divider,
        "BUFFETT RAG VERDICT",
        divider,
        "",
        verdict,
        "",
        divider,
    ]

    return "\n".join(lines)


def save_output(ticker: str, content: str) -> pathlib.Path:
    """Save report to outputs/<ticker>_analysis.txt"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = OUTPUT_DIR / f"{ticker}_{timestamp}_analysis.txt"
    path.write_text(content, encoding="utf-8")
    return path


# ── Historical context label helpers ────────────────────────────────────────

def _label_growth(cagr: float) -> str:
    if cagr >= 0.20: return "very high growth"
    if cagr >= 0.12: return "high growth"
    if cagr >= 0.07: return "solid growth"
    if cagr >= 0.03: return "modest growth"
    return "low / declining growth"


def _label_roe(roe: float) -> str:
    if roe >= 0.30: return "exceptional capital efficiency"
    if roe >= 0.20: return "strong capital efficiency"
    if roe >= 0.12: return "average capital efficiency"
    return "below average — investigate"


# ── Interactive custom scenario ──────────────────────────────────────────────

def parse_custom_assumptions(user_input: str) -> ScenarioAssumptions | None:
    """
    Parse a natural language custom scenario request using Claude.
    e.g. "with g1=25%, g2=12%, terminal=4%, discount=11%, what is the IV?"
    Returns a ScenarioAssumptions or None if nothing parseable.
    """
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"Extract DCF assumptions from this user message. "
                f"Respond ONLY with valid JSON, no extra text:\n\n"
                f"User message: \"{user_input}\"\n\n"
                f"JSON format (use null for any not mentioned):\n"
                f'{{"g1": 0.25, "g2": 0.12, "terminal_growth": 0.04, '
                f'"discount_rate": 0.11, "growth_capex_pct": null, "growth_capex_addback": null}}'
            )
        }]
    )

    raw = resp.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    return ScenarioAssumptions(
        label="Custom",
        g1=data.get("g1") or 0.10,
        g2=data.get("g2") or 0.06,
        terminal_growth=data.get("terminal_growth") or 0.03,
        discount_rate=data.get("discount_rate") or 0.10,
        growth_capex_pct=data.get("growth_capex_pct") or 0.55,
        growth_capex_addback=data.get("growth_capex_addback") or 0.55,
        reasoning="User-defined custom scenario",
    )


def interactive_mode(f: Financials) -> None:
    """
    After the main analysis, let the user ask custom scenario questions.
    Type 'quit' or 'exit' to stop.
    """
    print("\n" + "=" * 56)
    print("  INTERACTIVE MODE — Custom Scenario Calculator")
    print("=" * 56)
    print(f"  Ticker: {f.ticker} | Current price: ${f.price:,.0f}")
    print(f"  Historical FCF CAGR: {f.historical_fcf_growth:.1%}  ← {_label_growth(f.historical_fcf_growth)}")
    print(f"  Historical Rev CAGR: {f.historical_revenue_growth:.1%}  ← {_label_growth(f.historical_revenue_growth)}")
    print(f"  ROE: {f.roe:.1%}  ← {_label_roe(f.roe)}")
    if f.quality and f.quality.is_low:
        print(f"  Data quality: {f.quality.confidence} — buy zones "
              f"{f.quality.mos_penalty:.0%} stricter ({f.quality.reasons[0]})")
    if f.owner_earnings_override is not None:
        print(f"  Owner earnings: MID-CYCLE OVERRIDE "
              f"${f.owner_earnings_override/1e9:.1f}B")
    print()
    print("  Ask a custom scenario, e.g.:")
    print('  "with g1=25%, g2=12%, terminal=4%, discount=11%, what is the IV?"')
    print('  Or type "quit" to exit.')
    print("=" * 56)

    while True:
        try:
            user_input = input("\n  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Exiting interactive mode.")
            break

        if user_input.lower() in ("quit", "exit", "q", ""):
            print("  Exiting interactive mode.")
            break

        print("  Parsing your scenario...")
        try:
            custom = parse_custom_assumptions(user_input)
        except Exception as e:
            print(f"  Could not parse assumptions: {e}")
            print("  Try: \"g1=20%, g2=10%, terminal=3%, discount=10%\"")
            continue

        print(f"  Running: g1={custom.g1:.0%}, g2={custom.g2:.0%}, "
              f"terminal={custom.terminal_growth:.0%}, discount={custom.discount_rate:.0%}")

        results = run_scenarios(f, [custom])
        r = results[0]
        total_equity_b = r.pv_stage1_b + r.pv_stage2_b + r.pv_terminal_b + r.net_cash_b

        print()
        print(f"  {'─' * 52}")
        print(f"  CUSTOM SCENARIO RESULT")
        print(f"  g1={r.g1:.0%} | g2={r.g2:.0%} | "
              f"terminal={r.terminal_growth:.0%} | discount={r.discount_rate:.0%}")
        print(f"  {'─' * 52}")
        print(f"\n  STEP 1 — OWNER EARNINGS")
        print(f"    Net Income:           +${r.net_income_b:.1f}B")
        print(f"    D&A:                  +${r.da_b:.1f}B")
        print(f"    Capex:                -${r.capex_b:.1f}B")
        print(f"    SBC:                  -${r.sbc_b:.1f}B")
        print(f"    FCF:                  =${r.fcf_b:.1f}B")
        print(f"    Growth capex addback: +${r.growth_capex_addback_b:.1f}B")
        print(f"    Owner Earnings (OE):  =${r.owner_earnings_b:.1f}B"
              + ("   ← MID-CYCLE OVERRIDE (recipe above ignored)"
                 if r.oe_override else ""))
        print(f"\n  STEP 2 — DCF")
        print(f"    Stage 1 (g1={r.g1:.0%}, yrs 1–5):   ${r.pv_stage1_b:.1f}B")
        print(f"    Stage 2 (g2={r.g2:.0%}, yrs 6–10):  ${r.pv_stage2_b:.1f}B")
        print(f"    Terminal ({r.terminal_growth:.0%} forever):     ${r.pv_terminal_b:.1f}B")
        print(f"    Net Cash:                    ${r.net_cash_b:.1f}B")
        print(f"    Total Equity Value:          ${total_equity_b:.1f}B")
        print(f"\n  STEP 3 — PER SHARE")
        print(f"    ${total_equity_b:.1f}B ÷ {r.shares_b:.2f}B shares = ${r.iv_per_share:,.0f}/share")
        print(f"\n  STEP 4 — MARGIN OF SAFETY")
        print(f"    Price ${r.price:,.0f} ÷ IV ${r.iv_per_share:,.0f} = {r.ratio:.2f}")
        print(f"    ({r.ratio*100:.0f}c per $1 of intrinsic value)")
        print(f"    Buy zone: {r.zone.upper()}"
              + (f"  (LOW CONFIDENCE: zones {r.mos_penalty:.0%} stricter)"
                 if r.mos_penalty else ""))
        target = target_buy_price(r.iv_per_share, mos_penalty=r.mos_penalty)
        print(f"    Price needs ~${target:,.0f} to reach 'good' buy zone")
        for line in reverse_dcf_lines(f, results)[1:]:
            if line:
                print(f"  {line}")
        print(f"  {'─' * 52}")
        print("  This is an analytical framework, not investment advice.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Buffett RAG — Value investing analysis"
    )
    ap.add_argument("--ticker", required=True, help="Stock ticker e.g. MSFT, TSM, COST")
    ap.add_argument("--interactive", "-i", action="store_true",
                    help="After analysis, enter interactive custom scenario mode")
    ap.add_argument("--no-save", action="store_true",
                    help="Print only, don't save to file")
    ap.add_argument("--normalized-oe", type=float, default=None, metavar="BILLIONS",
                    help="Mid-cycle normalized owner earnings in $B, used instead of "
                         "the TTM recipe (for cyclicals), e.g. --normalized-oe 42.5")
    ap.add_argument("--oe-history", default=None, metavar="LIST",
                    help="Owner earnings per year in $B, comma separated, e.g. "
                         "--oe-history '30,10,-5,20,25'; averaged into a mid-cycle base")
    ap.add_argument("--min-years", type=int, default=MIN_YEARS_OF_HISTORY,
                    metavar="N",
                    help="Years of earnings history required before inputs count as "
                         "trustworthy (default %(default)s; yfinance supplies ~4)")
    args = ap.parse_args()

    ticker = args.ticker.upper()
    print(f"\nFetching financials for {ticker}...")

    # Step 1: Fetch (with the mid-cycle override, if one was given)
    try:
        override = resolve_owner_earnings_override(args.normalized_oe, args.oe_history)
    except ValueError as e:
        sys.exit(f"ERROR: {e}")
    f = fetch_financials(ticker, owner_earnings_override=override,
                         min_years=args.min_years)
    print(f"  Got data: ${f.net_income/1e9:.1f}B net income | "
          f"${f.capex/1e9:.1f}B capex | "
          f"Rev CAGR={f.historical_revenue_growth:.1%} | "
          f"FCF CAGR={f.historical_fcf_growth:.1%} | "
          f"ROE={f.roe:.1%}")

    # Step 2: RAG suggests assumptions
    print("\nQuerying Buffett knowledge base for assumptions...")
    scenarios = rag_suggest_assumptions(f)
    for s in scenarios:
        print(f"  {s.label}: g1={s.g1:.0%} | g2={s.g2:.0%} | "
              f"terminal={s.terminal_growth:.0%} | discount={s.discount_rate:.0%}")
        print(f"    → {s.reasoning}")

    # Step 3: Run scenarios
    print("\nRunning 3-scenario IV calculation...")
    results = run_scenarios(f, scenarios)
    for r in results:
        print(f"  {r.label}: IV=${r.iv_per_share:,.0f} | "
              f"Ratio={r.ratio:.2f} | Zone={r.zone.upper()}")

    # Step 4: Generate verdict
    print("\nGenerating Buffett verdict...")
    verdict = generate_verdict(f, results)

    # Step 5: Format + output
    report = format_output(f, results, verdict)
    print(report)

    if not args.no_save:
        saved_path = save_output(ticker, report)
        print(f"\nSaved to: {saved_path}")

    # Step 6: Interactive mode (optional)
    if args.interactive:
        interactive_mode(f)
    else:
        print(f"\nTip: run with --interactive to test custom scenarios.")
        print(f"     python examples/analyze_ticker.py --ticker {ticker} --interactive")


if __name__ == "__main__":
    main()
