"""
End-to-end example: NUMBERS -> MATH -> VERDICT.

This script IS the "someone" that calls financials.py. It presses the calculator buttons
by feeding in a company's numbers, then prints a Buffett-style verdict.

By default it uses built-in SAMPLE numbers, so it runs with NO network and NO API key:

    python examples/analyze_ticker.py

To pull live numbers from yfinance instead (rough template — field names drift over time):

    python examples/analyze_ticker.py --ticker COST

Note: the sample numbers are illustrative, not researched intrinsic values. The point is to
see the data flow, not to trade on this output. This is an analytical framework, not advice.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from dataclasses import dataclass

# Let this file run directly (python examples/analyze_ticker.py) by putting the repo root
# on the path so `from src...` works.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.financials import (  # noqa: E402
    buy_zone,
    intrinsic_value_per_share,
    margin_of_safety,
    owner_earnings,
)


@dataclass
class CompanyInputs:
    """Every number the math needs. In real life these come from SEC filings / yfinance."""
    name: str
    ticker: str
    price: float
    net_income: float
    depreciation_amortization: float
    capex: float                       # total capex
    stock_based_comp: float
    growth_capex: float                # the growth portion of capex
    growth_capex_addback_pct: float
    shares_outstanding: float
    net_cash: float
    g1: float                          # high-growth rate, years 1-5
    g2: float                          # moderate-growth rate, years 6-10
    terminal_growth: float
    discount_rate: float


# Illustrative numbers for demonstration only (NOT researched IVs).
SAMPLE = CompanyInputs(
    name="Costco (illustrative)", ticker="COST", price=912.0,
    net_income=7_400_000_000, depreciation_amortization=2_200_000_000,
    capex=4_700_000_000, stock_based_comp=850_000_000,
    growth_capex=2_000_000_000, growth_capex_addback_pct=0.50,
    shares_outstanding=443_000_000, net_cash=10_000_000_000,
    g1=0.09, g2=0.06, terminal_growth=0.03, discount_rate=0.09,
)


def make_verdict(c: CompanyInputs) -> str:
    """Run the numbers through the deterministic math and format a verdict card."""
    oe = owner_earnings(
        c.net_income, c.depreciation_amortization, c.capex,
        stock_based_comp=c.stock_based_comp,
        growth_capex=c.growth_capex,
        growth_capex_addback_pct=c.growth_capex_addback_pct,
    )
    iv = intrinsic_value_per_share(
        oe, c.shares_outstanding, c.g1, c.g2, c.terminal_growth,
        c.discount_rate, net_cash=c.net_cash,
    )
    ratio = margin_of_safety(c.price, iv)
    zone = buy_zone(ratio)

    bn = 1_000_000_000
    return (
        f"\n{c.name} ({c.ticker}) — Buffett-style read\n"
        + "=" * 46 + "\n"
        f"Owner earnings:    ${oe / bn:,.1f}B/yr\n"
        f"Intrinsic value:   ${iv:,.0f} / share\n"
        f"Current price:     ${c.price:,.0f} / share\n"
        f"Cents per $1 IV:   {ratio:.2f}  ({ratio * 100:.0f}c per dollar of value)\n"
        f"Buy zone:          {zone.upper()}\n"
        + "=" * 46 + "\n"
        "This is an analytical framework, not investment advice.\n"
    )


def from_yfinance(ticker: str) -> CompanyInputs:
    """Best-effort template that maps yfinance data into CompanyInputs.

    yfinance's field names and shapes change over time, so treat this as a STARTING POINT,
    not a finished pipeline — verify each number against the actual SEC filing. Growth
    rates and the maintenance/growth capex split are YOUR judgment, not something yfinance
    can hand you, so reasonable placeholders are used here.
    """
    import yfinance as yf

    t = yf.Ticker(ticker)
    info = t.info
    fin = t.financials          # income statement (columns = years)
    cf = t.cashflow             # cash-flow statement
    bs = t.balance_sheet        # balance sheet

    def latest(frame, *names):
        for n in names:
            if n in frame.index:
                return float(frame.loc[n].iloc[0])
        raise KeyError(f"None of {names} found — yfinance schema may have changed")

    net_income = latest(fin, "Net Income", "Net Income Common Stockholders")
    dep = latest(cf, "Depreciation And Amortization", "Depreciation")
    capex = abs(latest(cf, "Capital Expenditure", "Capital Expenditures"))
    cash = latest(bs, "Cash And Cash Equivalents", "Cash")
    debt = latest(bs, "Total Debt") if "Total Debt" in bs.index else 0.0
    shares = float(info.get("sharesOutstanding") or 0)
    price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0)

    if shares <= 0:
        raise ValueError("yfinance returned no share count — can't value per share")

    return CompanyInputs(
        name=info.get("shortName", ticker), ticker=ticker, price=price,
        net_income=net_income, depreciation_amortization=dep, capex=capex,
        stock_based_comp=0.0,                 # often needs the 10-K; left at 0 here
        growth_capex=capex * 0.5,             # placeholder split — YOUR judgment call
        growth_capex_addback_pct=0.5,
        shares_outstanding=shares, net_cash=cash - debt,
        g1=0.08, g2=0.05, terminal_growth=0.03, discount_rate=0.10,  # placeholders
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", help="pull live numbers from yfinance instead of the sample")
    args = ap.parse_args()

    if args.ticker:
        try:
            company = from_yfinance(args.ticker)
        except Exception as e:
            print(f"Could not build inputs from yfinance for {args.ticker}: {e}")
            print("Falling back to the built-in sample.\n")
            company = SAMPLE
    else:
        company = SAMPLE

    print(make_verdict(company))


if __name__ == "__main__":
    main()
