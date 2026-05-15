"""Deterministic stress scenarios for personal finance risk analysis."""

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from src.config.schema import FinanceBook

StressStatus = Literal["PASS", "FAIL"]


@dataclass
class StressTestResult:
    """Structured output for a single deterministic stress scenario.

    ``runway_days`` is ``math.inf`` when the stressed daily burn is non-positive
    (income still covers outflows even under the scenario).
    ``months_to_insolvency`` mirrors that value via ``math.ceil(runway_days / 30)``.
    """

    scenario_name: str
    parameters: dict[str, Any]
    runway_days: float
    months_to_insolvency: float
    status: StressStatus


def _compute_runway(cash: float, daily_burn: float) -> float:
    """Return cash/daily_burn, or inf when burn is non-positive."""
    if daily_burn <= 0:
        return math.inf
    return cash / daily_burn


def _months(runway_days: float) -> float:
    """Return ceil(runway_days / 30), preserving inf."""
    if math.isinf(runway_days):
        return math.inf
    return float(math.ceil(runway_days / 30))


def stress_income_drop(
    book: FinanceBook,
    pct_drop: float,
    buffer_days: float = 90,
) -> StressTestResult:
    """Scenario A – reduce all income streams by *pct_drop* fraction.

    Args:
        book: Personal finance snapshot.
        pct_drop: Fractional income reduction, e.g. 0.20 for a 20 % drop.
        buffer_days: Minimum runway days required to PASS.
    """
    reduced_income = book.total_monthly_income() * (1.0 - pct_drop)
    daily_burn = (book.total_monthly_outflows() - reduced_income) / 30
    runway = _compute_runway(book.balance_sheet.cash, daily_burn)
    return StressTestResult(
        scenario_name="income_drop",
        parameters={"pct_drop": pct_drop},
        runway_days=runway,
        months_to_insolvency=_months(runway),
        status="PASS" if runway >= buffer_days else "FAIL",
    )


def stress_income_delay(
    book: FinanceBook,
    delay_months: int,
    buffer_days: float = 90,
) -> StressTestResult:
    """Scenario B – income is zero for *delay_months* months, then resumes.

    Two analytical phases are computed without a day-by-day loop:

    * **Phase 1** (``delay_months * 30`` days): burn = outflows / 30 (no income).
      If cash is exhausted before the delay ends, insolvency occurs in this phase.
    * **Phase 2**: normal burn = (outflows - income) / 30 resumes on whatever
      cash remains.  If normal burn is non-positive, runway extends to infinity.

    Args:
        book: Personal finance snapshot.
        delay_months: Number of zero-income months.
        buffer_days: Minimum runway days required to PASS.
    """
    outflows = book.total_monthly_outflows()
    income = book.total_monthly_income()
    cash = book.balance_sheet.cash

    phase1_days = float(delay_months * 30)
    burn_p1 = outflows / 30

    if burn_p1 > 0:
        phase1_runway = cash / burn_p1
        if phase1_runway < phase1_days:
            runway = phase1_runway
            return StressTestResult(
                scenario_name="income_delay",
                parameters={"delay_months": delay_months},
                runway_days=runway,
                months_to_insolvency=_months(runway),
                status="PASS" if runway >= buffer_days else "FAIL",
            )

    cash_after_delay = cash - burn_p1 * phase1_days

    burn_p2 = (outflows - income) / 30
    if burn_p2 <= 0:
        runway = math.inf
    else:
        runway = phase1_days + cash_after_delay / burn_p2

    return StressTestResult(
        scenario_name="income_delay",
        parameters={"delay_months": delay_months},
        runway_days=runway,
        months_to_insolvency=_months(runway),
        status="PASS" if runway >= buffer_days else "FAIL",
    )


def stress_one_time_shock(
    book: FinanceBook,
    shock_amount: float,
    buffer_days: float = 90,
) -> StressTestResult:
    """Scenario C – apply a one-time immediate expense.

    Cash is reduced by *shock_amount*.  If the shock exceeds available cash the
    remainder zeroes out (the shortfall implicitly becomes debt, but cash cannot
    go negative).  Runway is then computed against the normal daily burn.

    Args:
        book: Personal finance snapshot.
        shock_amount: Immediate one-time expense.
        buffer_days: Minimum runway days required to PASS.
    """
    effective_cash = max(0.0, book.balance_sheet.cash - shock_amount)
    daily_burn = (book.total_monthly_outflows() - book.total_monthly_income()) / 30
    runway = _compute_runway(effective_cash, daily_burn)
    return StressTestResult(
        scenario_name="one_time_shock",
        parameters={"shock_amount": shock_amount},
        runway_days=runway,
        months_to_insolvency=_months(runway),
        status="PASS" if runway >= buffer_days else "FAIL",
    )
