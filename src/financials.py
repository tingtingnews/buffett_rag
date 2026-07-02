"""
Deterministic financial math: owner earnings, DCF intrinsic value, margin of safety.

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


def buy_zone(ratio: float) -> str:
    """Map a price/IV ratio to the buy-zone label from the ValueOS framework.

    <=0.70 ideal | <=0.75 good | <=0.80 acceptable | <=0.95 accumulate cautiously
    | <=1.00 hold — do not add | <=1.20 do not buy | >1.20 consider trimming
    """
    if ratio <= 0.70:
        return "ideal"
    if ratio <= 0.75:
        return "good"
    if ratio <= 0.80:
        return "acceptable"
    if ratio <= 0.95:
        return "accumulate cautiously"
    if ratio <= 1.00:
        return "hold — do not add"
    if ratio <= 1.20:
        return "do not buy"
    return "consider trimming"
