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
    LOW_CONFIDENCE_MOS_PENALTY,
    NORMAL_CONFIDENCE,
    assess_data_quality,
    buy_zone,
    implied_g1,
    intrinsic_value_per_share,
    margin_of_safety,
    mid_cycle_owner_earnings,
    owner_earnings,
    target_buy_price,
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


def test_buy_zone_penalty_widens_every_zone():
    # A 10c penalty moves each threshold down by 10c: 0.74 was "good", now it isn't.
    assert buy_zone(0.74) == "good"
    assert buy_zone(0.74, mos_penalty=0.10) == "accumulate cautiously"
    assert buy_zone(0.60, mos_penalty=0.10) == "ideal"
    assert buy_zone(0.65, mos_penalty=0.10) == "good"


def test_buy_zone_rejects_bad_penalty():
    with pytest.raises(ValueError):
        buy_zone(0.70, mos_penalty=1.0)
    with pytest.raises(ValueError):
        buy_zone(0.70, mos_penalty=-0.01)


# ------------------------------ target_buy_price ---------------------------

def test_target_buy_price_default_is_good_zone():
    assert math.isclose(target_buy_price(400), 300.0)


def test_target_buy_price_penalty_demands_a_lower_price():
    assert math.isclose(target_buy_price(400, mos_penalty=0.10), 260.0)


def test_target_buy_price_rejects_bad_inputs():
    with pytest.raises(ValueError):
        target_buy_price(0)
    with pytest.raises(ValueError):
        target_buy_price(400, zone_ratio=0.10, mos_penalty=0.10)


# --------------------------------- implied_g1 -------------------------------

def test_implied_g1_inverts_the_dcf():
    # Same hand-calculated case as test_dcf_hand_calculated_case: flat earnings of
    # 100 with zero growth and a 10% discount rate are worth exactly 100/share,
    # so a price of 100 implies g1 = 0%.
    g = implied_g1(price=100.0, base_owner_earnings=100, shares_outstanding=10,
                   g2=0.0, terminal_growth=0.0, discount_rate=0.10)
    assert math.isclose(g, 0.0, abs_tol=1e-6)


def test_implied_g1_round_trips_through_the_forward_dcf():
    # Value the business at a known g1, then ask what growth that value implies.
    inputs = dict(base_owner_earnings=50e9, shares_outstanding=2e9,
                  g2=0.09, terminal_growth=0.04, discount_rate=0.10, net_cash=-6.5e9)
    iv = intrinsic_value_per_share(g1=0.13, **inputs)
    assert math.isclose(implied_g1(price=iv, **inputs), 0.13, abs_tol=1e-6)


def test_implied_g1_rises_with_price():
    inputs = dict(base_owner_earnings=100, shares_outstanding=10,
                  g2=0.05, terminal_growth=0.03, discount_rate=0.10)
    assert implied_g1(price=200, **inputs) > implied_g1(price=150, **inputs)


def test_implied_g1_rejects_nonpositive_base_earnings():
    # A loss-making base has no growth rate that explains any positive price.
    with pytest.raises(ValueError):
        implied_g1(price=100, base_owner_earnings=-5, shares_outstanding=10,
                   g2=0.05, terminal_growth=0.03, discount_rate=0.10)


def test_implied_g1_rejects_price_outside_the_bracket():
    inputs = dict(base_owner_earnings=100, shares_outstanding=10,
                  g2=0.05, terminal_growth=0.03, discount_rate=0.10)
    with pytest.raises(ValueError, match="above intrinsic value"):
        implied_g1(price=1e9, **inputs)
    with pytest.raises(ValueError, match="below intrinsic value"):
        implied_g1(price=0.01, **inputs)


def test_implied_g1_rejects_bad_bounds_and_price():
    inputs = dict(base_owner_earnings=100, shares_outstanding=10,
                  g2=0.05, terminal_growth=0.03, discount_rate=0.10)
    with pytest.raises(ValueError):
        implied_g1(price=0, **inputs)
    with pytest.raises(ValueError):
        implied_g1(price=100, bounds=(0.5, 0.1), **inputs)


# -------------------------- mid_cycle_owner_earnings ------------------------

def test_mid_cycle_owner_earnings_averages_the_cycle():
    # A peak-to-trough semi cycle normalises to the middle, not the latest year.
    assert math.isclose(mid_cycle_owner_earnings([30, 10, -5, 20, 25]), 16.0)


def test_mid_cycle_owner_earnings_rejects_empty_history():
    with pytest.raises(ValueError):
        mid_cycle_owner_earnings([])


def test_mid_cycle_base_values_a_cyclical_below_its_peak():
    # Capitalising the peak year overstates a cyclical's intrinsic value.
    cycle = [30, 10, -5, 20, 25]
    common = dict(shares_outstanding=10, g1=0.05, g2=0.03,
                  terminal_growth=0.02, discount_rate=0.10)
    peak_iv = intrinsic_value_per_share(base_owner_earnings=max(cycle), **common)
    mid_iv = intrinsic_value_per_share(
        base_owner_earnings=mid_cycle_owner_earnings(cycle), **common)
    assert mid_iv < peak_iv


# ----------------------------- assess_data_quality --------------------------

def test_data_quality_normal_when_history_is_long_and_positive():
    q = assess_data_quality([10, 12, 14, 16, 18])
    assert q.confidence == NORMAL_CONFIDENCE
    assert not q.is_low
    assert q.reasons == ()
    assert q.mos_penalty == 0.0


def test_data_quality_flags_short_history():
    q = assess_data_quality([10, 12, 14])
    assert q.is_low
    assert q.years == 3
    assert q.mos_penalty == LOW_CONFIDENCE_MOS_PENALTY
    assert any("3 year(s)" in r for r in q.reasons)


def test_data_quality_flags_sign_flips_even_with_long_history():
    q = assess_data_quality([10, -2, 14, 16, 18, 20])
    assert q.is_low
    assert q.negative_years == 1
    assert any("swing between positive and negative" in r for r in q.reasons)


def test_data_quality_flags_all_negative_history():
    q = assess_data_quality([-1, -2, -3, -4, -5])
    assert q.is_low
    assert any("every year" in r for r in q.reasons)


def test_data_quality_empty_history_is_low_confidence():
    q = assess_data_quality()
    assert q.is_low
    assert q.years == 0


def test_data_quality_hand_verified_excuses_missing_history_but_not_sign_flips():
    # Canonical hand-checked inputs carry no multi-year series; that alone is fine.
    assert assess_data_quality(hand_verified=True).confidence == NORMAL_CONFIDENCE
    assert assess_data_quality([10, -2], hand_verified=True).is_low


def test_data_quality_extra_reasons_force_low_confidence():
    q = assess_data_quality([10, 12, 14, 16, 18],
                            extra_reasons=["cyclical business valued on TTM earnings"])
    assert q.is_low
    assert "cyclical business valued on TTM earnings" in q.reasons


def test_low_confidence_penalty_pushes_a_buy_out_of_the_buy_zone():
    # The end-to-end point of the flag: the same price/IV is no longer a buy.
    ratio = margin_of_safety(300, 400)       # 0.75
    q = assess_data_quality([10, 12, 14])    # thin history -> LOW CONFIDENCE
    assert buy_zone(ratio) == "good"
    assert buy_zone(ratio, mos_penalty=q.mos_penalty) == "accumulate cautiously"
