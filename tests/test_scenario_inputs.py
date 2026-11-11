"""
Unit tests for the app layer that feeds the deterministic math:
the mid-cycle owner-earnings override and the data-quality flag.

tests/test_financials.py proves the formulas. These prove the *inputs* reach them:
that an override really replaces the TTM recipe in every scenario, that a
LOW CONFIDENCE verdict really tightens the buy zones, and that the report renders
for a ticker whose growth capex is zero.

Nothing here touches the network or the Claude API.
"""

import pathlib
import sys

import pytest

# examples/ is a script folder, not a package, so put it on the path explicitly.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "examples"))

import analyze_ticker as at
from src.financials import LOW_CONFIDENCE, NORMAL_CONFIDENCE


def build(ticker: str, *, override=None, history=(), hand_verified=True, min_years=5):
    """A Financials for a canonical ticker, finalized exactly as fetch_financials does."""
    c = at.CANONICAL_FINANCIALS[ticker]
    a = at.CANONICAL_ASSUMPTIONS[ticker]
    f = at.Financials(
        name=ticker, ticker=ticker, price=at._FALLBACK_PRICE[ticker],
        net_income=c["net_income"], depreciation_amortization=c["da"],
        capex=c["capex"], stock_based_comp=c["sbc"],
        shares_outstanding=c["shares"], net_cash=c["net_cash"],
        historical_revenue_growth=a["g1"], historical_fcf_growth=a["g1"], roe=0.30,
        earnings_history=tuple(history), hand_verified=hand_verified,
    )
    return at._finalize(f, override, min_years)


# ------------------- resolve_owner_earnings_override ------------------------

def test_override_from_a_single_normalized_figure():
    assert at.resolve_owner_earnings_override(46.0, None) == pytest.approx(46.0e9)


def test_override_from_a_cycle_of_years_is_the_average():
    # $B in, absolute USD out: mean(40, 30, 55, 60, 45) = 46.0
    assert at.resolve_owner_earnings_override(None, "40,30,55,60,45") == pytest.approx(46.0e9)


def test_override_tolerates_spaces_and_negative_years():
    assert at.resolve_owner_earnings_override(None, "30, 10, -5, 20, 25") == pytest.approx(16.0e9)


def test_no_override_means_use_the_ttm_recipe():
    assert at.resolve_owner_earnings_override(None, None) is None
    assert at.resolve_owner_earnings_override(None, "") is None


def test_override_rejects_both_flags_at_once():
    with pytest.raises(ValueError, match="not both"):
        at.resolve_owner_earnings_override(21.8, "30,10")


def test_override_rejects_unparseable_history():
    with pytest.raises(ValueError, match="could not parse"):
        at.resolve_owner_earnings_override(None, "not,a,number")


# ----------------------- the override reaches the DCF -----------------------

def test_override_replaces_computed_owner_earnings_in_every_scenario():
    f = build("TSM", override=46.0e9)
    results = at.run_scenarios(f, at.rag_suggest_assumptions(f))
    assert len(results) == 3
    for r in results:
        assert r.oe_override is True
        assert r.owner_earnings_b == pytest.approx(46.0)


def test_without_an_override_owner_earnings_come_from_the_ttm_recipe():
    f = build("TSM")
    base = next(r for r in at.run_scenarios(f, at.rag_suggest_assumptions(f))
                if r.label == "Base")
    # NI 50.7 + D&A 48.0 - capex 54.0 - SBC 0 = 44.7, + 75% of 54.0 growth capex
    assert base.oe_override is False
    assert base.owner_earnings_b == pytest.approx(44.7 + 40.5, abs=0.05)


def test_mid_cycle_override_lowers_intrinsic_value_for_a_peak_earner():
    scenarios = at.rag_suggest_assumptions(build("TSM"))
    peak = next(r for r in at.run_scenarios(build("TSM"), scenarios) if r.label == "Base")
    mid = next(r for r in at.run_scenarios(build("TSM", override=46.0e9), scenarios)
               if r.label == "Base")
    assert mid.iv_per_share < peak.iv_per_share


# --------------------------- the data-quality flag --------------------------

def test_cyclical_ticker_without_an_override_is_low_confidence():
    f = build("TSM")
    assert f.quality.confidence == LOW_CONFIDENCE
    assert any("cyclical" in r for r in f.quality.reasons)


def test_supplying_a_mid_cycle_base_clears_the_cyclical_flag():
    f = build("TSM", override=46.0e9)
    assert f.quality.confidence == NORMAL_CONFIDENCE
    assert f.quality.mos_penalty == 0.0


def test_non_cyclical_hand_verified_ticker_is_normal_confidence():
    assert build("MSFT").quality.confidence == NORMAL_CONFIDENCE


def test_thin_or_sign_flipping_history_is_low_confidence():
    f = build("MSFT", history=(10e9, -2e9, 8e9), hand_verified=False)
    assert f.quality.confidence == LOW_CONFIDENCE
    assert len(f.quality.reasons) == 2       # short history AND a sign flip


def test_min_years_matches_the_depth_of_the_data_source():
    # yfinance supplies ~4 annual years, so a 4-year bar must not flag on length.
    history = (10e9, 11e9, 12e9, 13e9)
    assert build("MSFT", history=history, hand_verified=False,
                 min_years=5).quality.confidence == LOW_CONFIDENCE
    assert build("MSFT", history=history, hand_verified=False,
                 min_years=4).quality.confidence == NORMAL_CONFIDENCE


def test_low_confidence_penalty_tightens_the_buy_zone_in_the_result():
    scenarios = at.rag_suggest_assumptions(build("TSM"))
    flagged = next(r for r in at.run_scenarios(build("TSM"), scenarios)
                   if r.label == "Base")
    assert flagged.mos_penalty == 0.10
    # 0.73 of intrinsic value is "good" at face value, but not on shaky inputs.
    assert flagged.ratio == pytest.approx(0.73, abs=0.01)
    assert flagged.zone == "accumulate cautiously"


# ------------------------------- the report ---------------------------------

def test_report_renders_for_zero_growth_capex_tickers():
    # MCO's calibrated recipe adds back no growth capex: the percentage columns
    # have a zero base and must print "n/a" instead of dividing by zero.
    f = build("MCO")
    results = at.run_scenarios(f, at.rag_suggest_assumptions(f))
    report = at.format_output(f, results, "(verdict omitted)")
    assert "Addback (n/a of growth capex)" in report


def test_report_contains_the_new_sections():
    f = build("TSM")
    results = at.run_scenarios(f, at.rag_suggest_assumptions(f))
    report = at.format_output(f, results, "(verdict omitted)")
    assert "DATA QUALITY" in report
    assert LOW_CONFIDENCE in report
    assert "REVERSE DCF — WHAT THE PRICE ALREADY ASSUMES" in report
    assert "implied g1" in report


def test_report_marks_an_overridden_owner_earnings_base():
    f = build("TSM", override=46.0e9)
    results = at.run_scenarios(f, at.rag_suggest_assumptions(f))
    report = at.format_output(f, results, "(verdict omitted)")
    assert "MID-CYCLE OVERRIDE" in report


def test_reverse_dcf_lines_solve_for_every_scenario():
    f = build("MSFT")
    results = at.run_scenarios(f, at.rag_suggest_assumptions(f))
    lines = at.reverse_dcf_lines(f, results)
    solved = [l for l in lines if "implied g1" in l]
    assert len(solved) == 3
    assert not any("not solvable" in l for l in lines)
