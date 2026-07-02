"""
Unit tests for the deterministic financial math.

THIS IS THE QA CORE. Run with:  pytest -v

These tests prove the numbers are right regardless of what the AI says. In a fintech QA
role this is exactly the work: pin down the deterministic logic with tests, including the
edge cases and the error paths, so a future change can't silently break a calculation.
"""

import math

import pytest

from src.financials import (
    buy_zone,
    intrinsic_value_per_share,
    margin_of_safety,
    owner_earnings,
)


# ----------------------------- owner_earnings -----------------------------

def test_owner_earnings_basic():
    # 1000 + 200 - 300 - 50 = 850, plus 75% of 100 growth capex = +75 -> 925
    assert owner_earnings(1000, 200, 300, stock_based_comp=50,
                          growth_capex=100, growth_capex_addback_pct=0.75) == 925


def test_owner_earnings_defaults_to_plain_fcf():
    # No SBC, no growth capex add-back -> just NI + D&A - capex
    assert owner_earnings(100, 0, 0) == 100
    assert owner_earnings(500, 100, 200) == 400


def test_owner_earnings_rejects_bad_addback():
    with pytest.raises(ValueError):
        owner_earnings(100, 0, 0, growth_capex_addback_pct=1.5)
    with pytest.raises(ValueError):
        owner_earnings(100, 0, 0, growth_capex_addback_pct=-0.1)


# ------------------------ intrinsic_value_per_share ------------------------

def test_dcf_hand_calculated_case():
    # Flat earnings of 100, zero growth, 10% discount, 10 shares.
    # PV of 10 years of 100 + a zero-growth terminal value works out to exactly 1000,
    # so IV per share = 100.00.  (Hand-verified.)
    iv = intrinsic_value_per_share(
        base_owner_earnings=100, shares_outstanding=10,
        g1=0.0, g2=0.0, terminal_growth=0.0, discount_rate=0.10,
    )
    assert math.isclose(iv, 100.0, rel_tol=1e-9)


def test_dcf_higher_discount_rate_lowers_value():
    # A higher discount rate must always produce a lower intrinsic value.
    common = dict(base_owner_earnings=100, shares_outstanding=10,
                  g1=0.10, g2=0.05, terminal_growth=0.03)
    low_dr = intrinsic_value_per_share(**common, discount_rate=0.09)
    high_dr = intrinsic_value_per_share(**common, discount_rate=0.12)
    assert high_dr < low_dr


def test_dcf_net_cash_increases_value():
    common = dict(base_owner_earnings=100, shares_outstanding=10,
                  g1=0.05, g2=0.03, terminal_growth=0.02, discount_rate=0.10)
    assert (intrinsic_value_per_share(**common, net_cash=500)
            > intrinsic_value_per_share(**common, net_cash=0))


def test_dcf_rejects_terminal_ge_discount():
    with pytest.raises(ValueError):
        intrinsic_value_per_share(100, 10, 0.1, 0.05, terminal_growth=0.10,
                                  discount_rate=0.10)


def test_dcf_rejects_nonpositive_shares():
    with pytest.raises(ValueError):
        intrinsic_value_per_share(100, 0, 0.1, 0.05, 0.03, 0.10)


# ----------------------------- margin_of_safety ----------------------------

def test_margin_of_safety_ratio():
    assert math.isclose(margin_of_safety(77, 100), 0.77)
    assert math.isclose(margin_of_safety(120, 100), 1.20)


def test_margin_of_safety_rejects_bad_iv():
    with pytest.raises(ValueError):
        margin_of_safety(100, 0)


# -------------------------------- buy_zone ---------------------------------

@pytest.mark.parametrize("ratio,expected", [
    (0.65, "ideal"),
    (0.70, "ideal"),
    (0.74, "good"),
    (0.80, "acceptable"),
    (0.90, "accumulate cautiously"),
    (0.98, "hold — do not add"),
    (1.10, "do not buy"),
    (1.50, "consider trimming"),
])
def test_buy_zone_boundaries(ratio, expected):
    assert buy_zone(ratio) == expected


def test_buy_zone_matches_valueos_mco_example():
    # ValueOS: MCO bought at $432.20 against IV $560 = 77.2c -> "acceptable" buy zone.
    ratio = margin_of_safety(432.20, 560)
    assert math.isclose(ratio, 0.772, abs_tol=0.001)
    assert buy_zone(ratio) == "acceptable"
