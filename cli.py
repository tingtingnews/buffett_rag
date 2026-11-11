"""
Buffett RAG — Command Line Interface

After installing (pip install -e .):

  buffett analyze MSFT
  buffett analyze TSM --interactive
  buffett analyze TSM --oe-history 40,30,55,60,45      # mid-cycle base for a cyclical
  buffett scenario TSM --g1 25 --g2 12 --terminal 4 --discount 11
  buffett reverse TSM                                  # what growth does the price assume?
  buffett compare MSFT AAPL COST

This is an analytical framework, not investment advice.
"""

from __future__ import annotations

import os
import sys
import pathlib

# Repo root + examples on path
repo = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / "examples"))

# Load .env automatically so ANTHROPIC_API_KEY never needs manual setting
from dotenv import load_dotenv
load_dotenv(repo / ".env")

import click


# ── Shared options ───────────────────────────────────────────────────────────

def mid_cycle_options(command):
    """Add the mid-cycle owner-earnings override options to a command.

    For a cyclical business the TTM owner-earnings recipe capitalises a peak (or a
    trough) forever. These two options replace that base with your own normalized
    number: a single figure, or a cycle of years that gets averaged.
    """
    command = click.option(
        "--oe-history", default=None, metavar="LIST",
        help="Owner earnings per year in $B, comma separated "
             "(e.g. 40,30,55,60,45); averaged into a mid-cycle base",
    )(command)
    command = click.option(
        "--normalized-oe", default=None, type=float, metavar="BILLIONS",
        help="Mid-cycle normalized owner earnings in $B, used instead of the TTM recipe",
    )(command)
    return command


def min_years_option(command):
    """Add --min-years: how deep an earnings history the data-quality flag demands."""
    from src.financials import MIN_YEARS_OF_HISTORY

    return click.option(
        "--min-years", default=MIN_YEARS_OF_HISTORY, show_default=True, type=int,
        help="Years of earnings history required before inputs count as "
             "trustworthy (yfinance supplies ~4)",
    )(command)


def _resolve_override(normalized_oe, oe_history):
    """resolve_owner_earnings_override, with CLI-shaped error handling."""
    from analyze_ticker import resolve_owner_earnings_override

    try:
        return resolve_owner_earnings_override(normalized_oe, oe_history)
    except ValueError as e:
        raise click.UsageError(str(e)) from e


# ── CLI group ────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Buffett RAG — Value investing analysis powered by Buffett's letters."""
    pass


# ── Command 1: analyze ───────────────────────────────────────────────────────

@cli.command()
@click.argument("ticker")
@click.option("--interactive", "-i", is_flag=True,
              help="Enter interactive custom scenario mode after analysis")
@click.option("--no-save", is_flag=True,
              help="Print only, don't save to file")
@mid_cycle_options
@min_years_option
def analyze(ticker: str, interactive: bool, no_save: bool,
            normalized_oe: float | None, oe_history: str | None, min_years: int):
    """
    Run full Buffett RAG analysis on a ticker.

    Examples:

      buffett analyze MSFT

      buffett analyze TSM --interactive

      buffett analyze COST --no-save

      buffett analyze TSM --oe-history 40,30,55,60,45
    """
    from analyze_ticker import (
        fetch_financials,
        rag_suggest_assumptions,
        run_scenarios,
        generate_verdict,
        format_output,
        save_output,
    )

    # Import interactive_mode only if available (may not exist in older versions)
    try:
        from analyze_ticker import interactive_mode
        _has_interactive = True
    except ImportError:
        _has_interactive = False

    _check_api_key()
    override = _resolve_override(normalized_oe, oe_history)

    ticker = ticker.upper()
    click.echo(f"\nFetching financials for {ticker}...")

    f = fetch_financials(ticker, owner_earnings_override=override,
                         min_years=min_years)
    click.echo(f"  NI=${f.net_income/1e9:.1f}B | "
               f"Capex=${f.capex/1e9:.1f}B | "
               f"Rev CAGR={f.historical_revenue_growth:.1%} | "
               f"FCF CAGR={f.historical_fcf_growth:.1%} | "
               f"ROE={f.roe:.1%}")

    click.echo("Querying Buffett knowledge base...")
    scenarios = rag_suggest_assumptions(f)
    for s in scenarios:
        click.echo(f"  {s.label}: g1={s.g1:.0%} g2={s.g2:.0%} "
                   f"terminal={s.terminal_growth:.0%} discount={s.discount_rate:.0%}")

    click.echo("Running 3-scenario IV calculation...")
    results = run_scenarios(f, scenarios)
    for r in results:
        click.echo(f"  {r.label}: IV=${r.iv_per_share:,.0f} → {r.zone.upper()}")

    click.echo("Generating Buffett verdict...")
    verdict = generate_verdict(f, results)

    report = format_output(f, results, verdict)
    click.echo(report)

    if not no_save:
        path = save_output(ticker, report)
        click.echo(f"\nSaved to: {path}")

    if interactive:
        if _has_interactive:
            interactive_mode(f)
        else:
            click.echo("\nInteractive mode not available in your analyze_ticker.py.")
            click.echo("Please update examples/analyze_ticker.py to the latest version.")
    else:
        click.echo("\nTip: add --interactive to test custom scenarios.")
        click.echo("     buffett analyze TSM --interactive")


# ── Command 2: scenario ──────────────────────────────────────────────────────

@cli.command()
@click.argument("ticker")
@click.option("--g1",       required=True, type=float, help="High growth rate %  e.g. 25")
@click.option("--g2",       required=True, type=float, help="Moderate growth rate % e.g. 12")
@click.option("--terminal", required=True, type=float, help="Terminal growth rate % e.g. 4")
@click.option("--discount", required=True, type=float, help="Discount rate % e.g. 11")
@click.option("--capex-pct",    default=55.0, show_default=True,
              help="Growth capex as % of total capex e.g. 55")
@click.option("--addback-pct",  default=55.0, show_default=True,
              help="Growth capex addback % e.g. 55")
@mid_cycle_options
def scenario(ticker, g1, g2, terminal, discount, capex_pct, addback_pct,
             normalized_oe, oe_history):
    """
    Run a single custom scenario for a ticker.

    All rate inputs are in PERCENT (e.g. 25 means 25%, not 0.25).

    Examples:

      buffett scenario TSM --g1 25 --g2 12 --terminal 4 --discount 11

      buffett scenario MSFT --g1 14 --g2 8 --terminal 3 --discount 9 --capex-pct 65 --addback-pct 65
    """
    from analyze_ticker import (
        fetch_financials,
        ScenarioAssumptions,
        run_scenarios,
    )
    from src.financials import target_buy_price

    _check_api_key()
    override = _resolve_override(normalized_oe, oe_history)

    ticker = ticker.upper()
    click.echo(f"\nFetching financials for {ticker}...")
    f = fetch_financials(ticker, owner_earnings_override=override)
    click.echo(f"  Price=${f.price:,.0f} | NI=${f.net_income/1e9:.1f}B | "
               f"Capex=${f.capex/1e9:.1f}B")

    custom = ScenarioAssumptions(
        label="Custom",
        g1=g1 / 100,
        g2=g2 / 100,
        terminal_growth=terminal / 100,
        discount_rate=discount / 100,
        growth_capex_pct=capex_pct / 100,
        growth_capex_addback=addback_pct / 100,
        reasoning=f"User-defined: g1={g1}% g2={g2}% terminal={terminal}% discount={discount}%",
    )

    results = run_scenarios(f, [custom])
    r = results[0]
    total_equity_b = r.pv_stage1_b + r.pv_stage2_b + r.pv_terminal_b + r.net_cash_b

    click.echo(f"\n{'=' * 56}")
    click.echo(f"  {f.name} ({ticker}) — Custom Scenario")
    click.echo(f"  g1={g1:.0f}% | g2={g2:.0f}% | terminal={terminal:.0f}% | discount={discount:.0f}%")
    click.echo(f"{'=' * 56}")
    click.echo(f"\n  STEP 1 — OWNER EARNINGS")
    click.echo(f"    Net Income:           +${r.net_income_b:.1f}B")
    click.echo(f"    D&A:                  +${r.da_b:.1f}B")
    click.echo(f"    Capex:                -${r.capex_b:.1f}B")
    click.echo(f"    SBC:                  -${r.sbc_b:.1f}B")
    click.echo(f"    FCF:                  =${r.fcf_b:.1f}B")
    click.echo(f"    Growth capex addback: +${r.growth_capex_addback_b:.1f}B")
    click.echo(f"    Owner Earnings (OE):  =${r.owner_earnings_b:.1f}B"
               + ("   <- MID-CYCLE OVERRIDE (recipe above ignored)"
                  if r.oe_override else ""))
    click.echo(f"\n  STEP 2 — DCF")
    click.echo(f"    Stage 1 (g1={g1:.0f}%, yrs 1–5):   ${r.pv_stage1_b:.1f}B")
    click.echo(f"    Stage 2 (g2={g2:.0f}%, yrs 6–10):  ${r.pv_stage2_b:.1f}B")
    click.echo(f"    Terminal ({terminal:.0f}% forever):     ${r.pv_terminal_b:.1f}B")
    click.echo(f"    Net Cash:                    ${r.net_cash_b:.1f}B")
    click.echo(f"    Total Equity Value:          ${total_equity_b:.1f}B")
    click.echo(f"\n  STEP 3 — PER SHARE")
    click.echo(f"    ${total_equity_b:.1f}B ÷ {r.shares_b:.2f}B shares = ${r.iv_per_share:,.0f}/share")
    click.echo(f"\n  STEP 4 — MARGIN OF SAFETY")
    click.echo(f"    Price ${r.price:,.0f} ÷ IV ${r.iv_per_share:,.0f} = {r.ratio:.2f}")
    click.echo(f"    ({r.ratio*100:.0f}c per $1 of intrinsic value)")
    click.echo(f"    Buy zone: {r.zone.upper()}"
               + (f"  (LOW CONFIDENCE: zones {r.mos_penalty:.0%} stricter)"
                  if r.mos_penalty else ""))
    target = target_buy_price(r.iv_per_share, mos_penalty=r.mos_penalty)
    click.echo(f"    Price needs ~${target:,.0f} to reach 'good' buy zone")
    click.echo(f"\n  This is an analytical framework, not investment advice.")


# ── Command 3: reverse ───────────────────────────────────────────────────────

@cli.command()
@click.argument("ticker")
@click.option("--price", default=None, type=float,
              help="Price per share to explain  [default: the fetched price]")
@click.option("--g2", default=None, type=float,
              help="Years 6-10 growth %  [default: the ticker's calibrated g2, else 8]")
@click.option("--terminal", default=None, type=float,
              help="Terminal growth %  [default: calibrated, else 3]")
@click.option("--discount", default=None, type=float,
              help="Discount rate %  [default: calibrated, else 10]")
@click.option("--capex-pct", default=None, type=float,
              help="Growth capex as % of total capex  [default: calibrated, else 55]")
@click.option("--addback-pct", default=None, type=float,
              help="Growth capex addback %  [default: calibrated, else 55]")
@mid_cycle_options
@min_years_option
def reverse(ticker, price, g2, terminal, discount, capex_pct, addback_pct,
            normalized_oe, oe_history, min_years):
    """
    Reverse DCF: the stage-1 growth rate the current price already assumes.

    The forward DCF asks what a business is worth. This asks what you would have to
    believe to pay today's price — every other input is held fixed. No API key and
    no knowledge base needed; it is pure math.

    Examples:

      buffett reverse TSM

      buffett reverse MSFT --price 420 --discount 10

      buffett reverse TSM --oe-history 40,30,55,60,45
    """
    from analyze_ticker import CANONICAL_ASSUMPTIONS, fetch_financials
    from src.financials import implied_g1, owner_earnings

    override = _resolve_override(normalized_oe, oe_history)

    ticker = ticker.upper()
    click.echo(f"\nFetching financials for {ticker}...")
    f = fetch_financials(ticker, owner_earnings_override=override,
                         min_years=min_years)

    a = CANONICAL_ASSUMPTIONS.get(ticker, {})
    g2_r = g2 / 100 if g2 is not None else a.get("g2", 0.08)
    term_r = terminal / 100 if terminal is not None else a.get("terminal", 0.03)
    disc_r = discount / 100 if discount is not None else a.get("discount", 0.10)
    capex_r = capex_pct / 100 if capex_pct is not None else a.get("capex_pct", 0.55)
    addback_r = addback_pct / 100 if addback_pct is not None else a.get("addback", 0.55)
    price_r = price if price is not None else f.price

    if f.owner_earnings_override is not None:
        oe = f.owner_earnings_override
        oe_note = "mid-cycle override"
    else:
        oe = owner_earnings(
            net_income=f.net_income,
            depreciation_amortization=f.depreciation_amortization,
            capex=f.capex,
            stock_based_comp=f.stock_based_comp,
            growth_capex=f.capex * capex_r,
            growth_capex_addback_pct=addback_r,
        )
        oe_note = f"TTM recipe, {capex_r:.0%} growth capex at {addback_r:.0%} add-back"

    try:
        g = implied_g1(
            price=price_r,
            base_owner_earnings=oe,
            shares_outstanding=f.shares_outstanding,
            g2=g2_r,
            terminal_growth=term_r,
            discount_rate=disc_r,
            net_cash=f.net_cash,
        )
    except ValueError as e:
        raise click.ClickException(f"cannot solve for implied growth: {e}") from e

    click.echo(f"\n{'=' * 56}")
    click.echo(f"  {f.name} ({ticker}) — Reverse DCF")
    click.echo(f"{'=' * 56}")
    click.echo(f"\n  Price:                ${price_r:,.2f}/share")
    click.echo(f"  Owner earnings base:  ${oe/1e9:.1f}B  ({oe_note})")
    click.echo(f"  Held fixed:           g2={g2_r:.0%} | terminal={term_r:.0%} | "
               f"discount={disc_r:.0%} | net cash=${f.net_cash/1e9:.1f}B")
    click.echo(f"\n  -> Implied stage-1 growth (years 1-5): {g:.1%} per year")

    assumed = a.get("g1")
    if assumed is not None:
        gap = g - assumed
        if gap > 0.005:
            verdict = (f"the price assumes MORE growth than your calibrated "
                       f"{assumed:.0%} — the market is more optimistic than you")
        elif gap < -0.005:
            verdict = (f"the price assumes LESS growth than your calibrated "
                       f"{assumed:.0%} — the market is more pessimistic than you")
        else:
            verdict = f"the price matches your calibrated {assumed:.0%}"
        click.echo(f"     vs calibrated g1 {assumed:.0%} ({gap:+.1%}): {verdict}")

    if f.quality and f.quality.is_low:
        click.echo(f"\n  {f.quality.confidence}: this implied growth rests on shaky "
                   f"inputs —")
        for reason in f.quality.reasons:
            click.echo(f"    - {reason}")

    click.echo(f"\n  Judge that number, not the price: is {g:.1%} a year for five "
               f"years plausible")
    click.echo(f"  for this business?")
    click.echo(f"\n  This is an analytical framework, not investment advice.")


# ── Command 4: compare ───────────────────────────────────────────────────────

@cli.command()
@click.argument("tickers", nargs=-1, required=True)
def compare(tickers):
    """
    Compare multiple tickers side by side (Base case only).

    Example:

      buffett compare MSFT AAPL COST TSM
    """
    from analyze_ticker import (
        fetch_financials,
        rag_suggest_assumptions,
        run_scenarios,
    )

    _check_api_key()

    rows = []
    for ticker in [t.upper() for t in tickers]:
        click.echo(f"Analyzing {ticker}...")
        try:
            f = fetch_financials(ticker)
            scenarios = rag_suggest_assumptions(f)
            results = run_scenarios(f, scenarios)
            base = next(r for r in results if r.label == "Base")
            flag = "LOW CONF" if (f.quality and f.quality.is_low) else ""
            rows.append((ticker, f.price, base.iv_per_share, base.ratio,
                         base.zone, flag))
        except Exception as e:
            click.echo(f"  ERROR on {ticker}: {e}")

    if not rows:
        click.echo("No results.")
        return

    click.echo(f"\n{'=' * 70}")
    click.echo(f"  COMPARISON — Base Case Intrinsic Value")
    click.echo(f"{'=' * 70}")
    click.echo(f"  {'Ticker':<8} {'Price':>8} {'IV (Base)':>10} {'Price/IV':>10} "
               f"{'Zone':<25} {'Data':<9}")
    click.echo(f"  {'-'*74}")
    for ticker, price, iv, ratio, zone, flag in sorted(rows, key=lambda x: x[3]):
        click.echo(f"  {ticker:<8} ${price:>7,.0f} ${iv:>9,.0f} {ratio:>9.2f}x  "
                   f"{zone.upper():<25} {flag:<9}")
    click.echo(f"{'=' * 70}")
    click.echo("  Sorted by Price/IV ratio (cheapest first)")
    click.echo("  LOW CONF = thin or erratic inputs; its zone already demands "
               "more margin of safety")
    click.echo("  This is an analytical framework, not investment advice.")


# ── Helper ───────────────────────────────────────────────────────────────────

def _check_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        click.echo("ERROR: ANTHROPIC_API_KEY not set.", err=True)
        click.echo("Add it to your .env file as:  ANTHROPIC_API_KEY=sk-ant-...", err=True)
        click.echo("Get a key at: https://console.anthropic.com/settings/keys", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
