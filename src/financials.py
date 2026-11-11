"""
Deterministic financial math: owner earnings, DCF intrinsic value, reverse DCF,
margin of safety, buy zones, and the data-quality flag that widens them.

WHY THIS FILE MATTERS (the QA point)
------------------------------------
Everything here is DETERMINISTIC: the same inputs always produce the same output.
That makes it perfectly unit-testable (see tests/test_financials.py). The AI never
touches these numbers — it only explains them. Keeping the math separate from the AI
is the core QA design decision of this project: the part that must be *correct* is
isolated from the part that is merely *plausible*.

Formulas follow the method in data/knowledge_base/valueos_knowledge_base.md.
This is an analytical framework, not investment advice.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


def owner_earnings(
    net_income: float,
    depreciation_amortization: float,
    capex: float,
    stock_based_comp: float = 0.0,
    growth_capex: float = 0.0,
    growth_capex_addback_pct: float = 1.0,
) -> float:
    """Buffett's owner earnings (1986 definition), in the same currency unit as inputs.

    Starts from free cash flow (which subtracts ALL capex), then adds back the portion
    of *growth* capex that represents investment in future earnings rather than a cost
    of running today's business.

        free_cash_flow = net_income + D&A - capex - stock_based_comp
        owner_earnings = free_cash_flow + growth_capex * growth_capex_addback_pct

    Args:
        net_income:                reported net income (TTM actuals only — never guidance)
        depreciation_amortization: non-cash D&A added back
        capex:                     TOTAL capital expenditure (maintenance + growth)
        stock_based_comp:          stock-based compensation (a real cost; subtracted)
        growth_capex:              the growth portion of capex (investment in the future)
        growth_capex_addback_pct:  fraction of growth capex to add back (e.g. 0.75 for MSFT).
                                   Being below 1.0 is the conservative haircut.

    Returns:
        Owner earnings (float).

    Raises:
        ValueError: if growth_capex_addback_pct is outside [0, 1].
    """
    if not 0.0 <= growth_capex_addback_pct <= 1.0:
        raise ValueError("growth_capex_addback_pct must be between 0 and 1")
    free_cash_flow = net_income + depreciation_amortization - capex - stock_based_comp
    return free_cash_flow + growth_capex * growth_capex_addback_pct


def intrinsic_value_per_share(
    base_owner_earnings: float,
    shares_outstanding: float,
    g1: float,
    g2: float,
    terminal_growth: float,
    discount_rate: float,
    net_cash: float = 0.0,
    high_growth_years: int = 5,
    moderate_growth_years: int = 5,
) -> float:
    """Three-stage owner-earnings DCF -> intrinsic value PER SHARE.

    Stage 1: years 1..high_growth_years grow at g1.
    Stage 2: next moderate_growth_years grow at g2.
    Terminal: Gordon-growth terminal value on the year after stage 2, discounted back.
    Then add net cash (or subtract net debt) and divide by shares.

    All rates are decimals (e.g. 0.13 for 13%).

    Raises:
        ValueError: if shares_outstanding <= 0, or discount_rate <= terminal_growth
                    (the terminal formula diverges otherwise).
    """
    if shares_outstanding <= 0:
        raise ValueError("shares_outstanding must be positive")
    if discount_rate <= terminal_growth:
        raise ValueError("discount_rate must be greater than terminal_growth")

    earnings = base_owner_earnings
    pv_sum = 0.0
    year = 0

    for _ in range(high_growth_years):
        year += 1
        earnings *= (1 + g1)
        pv_sum += earnings / (1 + discount_rate) ** year

    for _ in range(moderate_growth_years):
        year += 1
        earnings *= (1 + g2)
        pv_sum += earnings / (1 + discount_rate) ** year

    terminal_earnings = earnings * (1 + terminal_growth)
    terminal_value = terminal_earnings / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / (1 + discount_rate) ** year

    equity_value = pv_sum + pv_terminal + net_cash
    return equity_value / shares_outstanding


def margin_of_safety(price: float, intrinsic_value: float) -> float:
    """Cents paid per $1 of intrinsic value = price / intrinsic_value.

    Below 1.0 means you're paying less than the business is worth (a discount).
    Raises ValueError if intrinsic_value <= 0.
    """
    if intrinsic_value <= 0:
        raise ValueError("intrinsic_value must be positive")
    return price / intrinsic_value


# ── Buy zones ────────────────────────────────────────────────────────────────

# (max price/IV ratio, label) from the ValueOS framework, cheapest zone first.
_BUY_ZONES: tuple[tuple[float, str], ...] = (
    (0.70, "ideal"),
    (0.75, "good"),
    (0.80, "acceptable"),
    (0.95, "accumulate cautiously"),
    (1.00, "hold — do not add"),
    (1.20, "do not buy"),
)


def buy_zone(ratio: float, mos_penalty: float = 0.0) -> str:
    """Map a price/IV ratio to the buy-zone label from the ValueOS framework.

    <=0.70 ideal | <=0.75 good | <=0.80 acceptable | <=0.95 accumulate cautiously
    | <=1.00 hold — do not add | <=1.20 do not buy | >1.20 consider trimming

    Args:
        ratio:       price / intrinsic value (see margin_of_safety).
        mos_penalty: extra margin of safety demanded because the inputs are shaky.
                     Every threshold moves down by this amount, so with a 0.10
                     penalty "ideal" requires 0.60 instead of 0.70. Size it with
                     assess_data_quality.

    Raises:
        ValueError: if mos_penalty is outside [0, 1).
    """
    if not 0.0 <= mos_penalty < 1.0:
        raise ValueError("mos_penalty must be in [0, 1)")
    for threshold, label in _BUY_ZONES:
        if ratio <= threshold - mos_penalty:
            return label
    return "consider trimming"


def target_buy_price(
    intrinsic_value: float,
    zone_ratio: float = 0.75,
    mos_penalty: float = 0.0,
) -> float:
    """Price at which a stock enters the zone whose ceiling is zone_ratio.

    Default 0.75 = the top of the "good" zone. A data-quality penalty lowers the
    price you may pay, which is the whole point of flagging bad inputs.

    Raises:
        ValueError: if intrinsic_value <= 0, or the penalty wipes out the zone.
    """
    if intrinsic_value <= 0:
        raise ValueError("intrinsic_value must be positive")
    effective = zone_ratio - mos_penalty
    if effective <= 0:
        raise ValueError("mos_penalty must be smaller than zone_ratio")
    return intrinsic_value * effective


# ── Reverse DCF: what growth does the current price already assume? ─────────

def implied_g1(
    price: float,
    base_owner_earnings: float,
    shares_outstanding: float,
    g2: float,
    terminal_growth: float,
    discount_rate: float,
    net_cash: float = 0.0,
    high_growth_years: int = 5,
    moderate_growth_years: int = 5,
    bounds: tuple[float, float] = (-0.90, 1.00),
    tolerance: float = 1e-9,
) -> float:
    """Reverse DCF: the stage-1 growth rate that makes intrinsic value equal price.

    The forward DCF asks "what is this worth?". This asks "what is the market
    already assuming?" — a number you can then judge as plausible or not. Every
    other input (g2, terminal growth, discount rate, net cash, share count) is
    held fixed, so the answer is only as meaningful as those are.

    Intrinsic value rises monotonically with g1 when owner earnings are positive,
    so the root is unique and found by bisection.

    Args:
        price:     the market price per share to explain.
        bounds:    (low, high) search bracket for g1, as decimals. The default
                   spans a 90% annual collapse to an annual doubling.
        tolerance: bracket width at which to stop, in g1 decimals.

    Returns:
        The implied g1 as a decimal (0.13 = 13%).

    Raises:
        ValueError: if price <= 0, base_owner_earnings <= 0, the bracket is
                    malformed, or price lies outside the value range the bracket
                    can produce (the message says which side).
    """
    if price <= 0:
        raise ValueError("price must be positive")
    if base_owner_earnings <= 0:
        raise ValueError(
            "base_owner_earnings must be positive to solve for implied growth"
        )
    low, high = bounds
    if low >= high:
        raise ValueError("bounds must be (low, high) with low < high")

    def value_at(g1: float) -> float:
        return intrinsic_value_per_share(
            base_owner_earnings=base_owner_earnings,
            shares_outstanding=shares_outstanding,
            g1=g1,
            g2=g2,
            terminal_growth=terminal_growth,
            discount_rate=discount_rate,
            net_cash=net_cash,
            high_growth_years=high_growth_years,
            moderate_growth_years=moderate_growth_years,
        )

    if value_at(low) > price:
        raise ValueError(
            f"price {price:.2f} is below intrinsic value even at g1={low:.0%}; "
            "the price implies a decline steeper than the search bracket allows"
        )
    if value_at(high) < price:
        raise ValueError(
            f"price {price:.2f} is above intrinsic value even at g1={high:.0%}; "
            "the price implies growth beyond the search bracket"
        )

    while high - low > tolerance:
        mid = (low + high) / 2
        if value_at(mid) < price:
            low = mid
        else:
            high = mid
    return (low + high) / 2


# ── Cyclicals: normalising owner earnings over a cycle ──────────────────────

def mid_cycle_owner_earnings(history: Sequence[float]) -> float:
    """Average owner earnings across the years supplied — a mid-cycle base.

    For a cyclical business the latest year is the wrong base: at the top of the
    cycle a DCF capitalises peak earnings forever, at the bottom it writes the
    company off. Feed this a full cycle (peak to peak, typically 5-10 years) and
    use the result as base_owner_earnings instead of the TTM figure. Negative
    years are kept — they are part of the cycle.

    Raises:
        ValueError: if history is empty.
    """
    values = [float(v) for v in history]
    if not values:
        raise ValueError("history must contain at least one year of owner earnings")
    return sum(values) / len(values)


# ── Data quality: how much to trust the inputs ───────────────────────────────

MIN_YEARS_OF_HISTORY = 5
LOW_CONFIDENCE_MOS_PENALTY = 0.10
LOW_CONFIDENCE = "LOW CONFIDENCE"
NORMAL_CONFIDENCE = "NORMAL"


@dataclass(frozen=True)
class DataQuality:
    """Verdict on the inputs feeding a valuation.

    confidence:     NORMAL_CONFIDENCE or LOW_CONFIDENCE.
    years:          years of earnings history examined.
    negative_years: how many of those were <= 0.
    reasons:        why confidence is low (empty when NORMAL).
    mos_penalty:    amount to subtract from every buy-zone threshold (see buy_zone).
    """
    confidence: str
    years: int
    negative_years: int
    reasons: tuple[str, ...]
    mos_penalty: float

    @property
    def is_low(self) -> bool:
        return self.confidence == LOW_CONFIDENCE


def assess_data_quality(
    earnings_history: Sequence[float] = (),
    min_years: int = MIN_YEARS_OF_HISTORY,
    hand_verified: bool = False,
    extra_reasons: Sequence[str] = (),
    penalty: float = LOW_CONFIDENCE_MOS_PENALTY,
) -> DataQuality:
    """Flag inputs too thin or too erratic to value with a single-point DCF.

    Two tests, both of them reasons a DCF quietly lies:
      1. Short history — under min_years of earnings means no cycle was observed.
      2. Sign flips — earnings that swing between positive and negative have no
         trend to extrapolate, and a growth rate off such a base is meaningless.

    A LOW CONFIDENCE verdict carries a margin-of-safety penalty: pass
    DataQuality.mos_penalty to buy_zone and target_buy_price so that a shaky
    valuation has to be cheaper before it counts as a buy.

    Args:
        earnings_history: earnings (or owner earnings) per year; order does not matter.
        min_years:        years of history required to see a cycle.
        hand_verified:    True when the inputs were checked by a human, which
                          excuses a missing history but not sign flips.
        extra_reasons:    caller-supplied reasons, e.g. "cyclical business valued on
                          TTM earnings". Any non-empty reason forces LOW CONFIDENCE.
        penalty:          extra margin of safety demanded when confidence is low.
    """
    values = [float(v) for v in earnings_history]
    years = len(values)
    negative_years = sum(1 for v in values if v <= 0)
    reasons: list[str] = []

    if not hand_verified and years < min_years:
        reasons.append(
            f"only {years} year(s) of earnings history (need {min_years} to see a cycle)"
        )
    if years and negative_years == years:
        reasons.append("every year of earnings history is negative or zero")
    elif negative_years:
        reasons.append(
            f"earnings swing between positive and negative "
            f"({negative_years} of {years} years negative)"
        )
    reasons.extend(str(r) for r in extra_reasons if r)

    confidence = LOW_CONFIDENCE if reasons else NORMAL_CONFIDENCE
    return DataQuality(
        confidence=confidence,
        years=years,
        negative_years=negative_years,
        reasons=tuple(reasons),
        mos_penalty=penalty if reasons else 0.0,
    )
