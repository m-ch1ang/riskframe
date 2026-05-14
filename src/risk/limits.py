"""Risk limit calculations."""

from dataclasses import dataclass
from typing import Literal

from src.config.schema import FinanceBook
from src.risk.liquidity import liquidity_runway

Basis = Literal["CASH_ONLY", "LIQUID_ASSETS"]


@dataclass
class LimitsResult:
    """Structured output for risk limit calculations."""

    min_runway_days: int
    required_buffer: float
    max_safe_spend: float
    basis: Basis


def max_safe_spend_today(
    book: FinanceBook,
    min_runway_days: int = 42,
    use_cash_only: bool = True,
) -> LimitsResult:
    """Compute the maximum amount that can be safely spent today.

    Reserves enough cash (or liquid assets) to cover ``min_runway_days`` of
    burn before allowing any discretionary spend.  When the book is cash-flow
    positive (``daily_burn <= 0``) the full available balance is spendable.
    """
    liq = liquidity_runway(book)
    daily_burn = liq.daily_burn
    available = book.balance_sheet.cash if use_cash_only else book.liquid_assets()
    basis: Basis = "CASH_ONLY" if use_cash_only else "LIQUID_ASSETS"

    if daily_burn <= 0:
        return LimitsResult(
            min_runway_days=min_runway_days,
            required_buffer=0.0,
            max_safe_spend=available,
            basis=basis,
        )

    required_buffer = min_runway_days * daily_burn
    max_safe_spend = max(0.0, available - required_buffer)

    return LimitsResult(
        min_runway_days=min_runway_days,
        required_buffer=required_buffer,
        max_safe_spend=max_safe_spend,
        basis=basis,
    )
