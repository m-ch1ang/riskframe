"""Leverage analytics for personal finance risk assessment."""

from dataclasses import dataclass, field
from typing import Optional

from src.config.schema import FinanceBook


@dataclass
class LeverageResult:
    """Structured output for leverage metric calculations.

    ``leverage_income_ratio`` is ``None`` when total monthly income is zero.
    ``fixed_coverage_ratio`` is ``None`` when total fixed outflows are zero.
    ``leverage_net_liquid`` is always computed; the net liquid worth denominator
    is clamped to ``1e-9`` to avoid division by zero.
    """

    leverage_income_ratio: Optional[float]
    leverage_net_liquid: float
    fixed_coverage_ratio: Optional[float]
    flags: list[str] = field(default_factory=list)


def leverage_metrics(book: FinanceBook) -> LeverageResult:
    """Compute leverage ratios and flag abnormal conditions.

    Metrics
    -------
    leverage_income_ratio
        ``total_monthly_outflows / total_monthly_income`` — how many times
        outflows exceed income.  ``None`` (and flagged) when income is zero.
    leverage_net_liquid
        ``total_monthly_outflows / max(net_liquid_worth, 1e-9)`` —
        institutional-style leverage proxy relative to net liquid position.
    fixed_coverage_ratio
        ``total_monthly_income / total_fixed_outflows`` — how well income
        covers committed fixed obligations.  ``None`` (and flagged) when
        fixed outflows are zero.
    """
    flags: list[str] = []

    income = book.total_monthly_income()
    outflows = book.total_monthly_outflows()
    fixed_outflows = book.total_fixed_outflows()
    net_liquid = book.net_liquid_worth()

    if income == 0:
        flags.append("income_zero")
        leverage_income_ratio: Optional[float] = None
    else:
        leverage_income_ratio = outflows / income

    if net_liquid <= 0:
        flags.append("net_liquid_nonpositive")
    leverage_net_liquid = outflows / max(net_liquid, 1e-9)

    if fixed_outflows == 0:
        flags.append("fixed_outflows_zero")
        fixed_coverage_ratio: Optional[float] = None
    else:
        fixed_coverage_ratio = income / fixed_outflows

    return LeverageResult(
        leverage_income_ratio=leverage_income_ratio,
        leverage_net_liquid=leverage_net_liquid,
        fixed_coverage_ratio=fixed_coverage_ratio,
        flags=flags,
    )
