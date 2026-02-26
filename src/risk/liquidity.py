"""Liquidity runway analytics."""

import math
from dataclasses import dataclass
from typing import Literal

from src.config.schema import FinanceBook

LiquidityStatus = Literal["SAFE", "WARN", "CRITICAL"]


@dataclass
class LiquidityResult:
    """Structured output for liquidity runway calculations.

    Infinite runway is represented as ``math.inf`` when ``daily_burn <= 0``.
    """

    daily_burn: float
    runway_days_cash_only: float
    runway_days_liquid_assets: float
    status: LiquidityStatus


def _status_from_cash_runway(runway_days_cash_only: float) -> LiquidityStatus:
    """Classify liquidity health from cash-only runway days."""
    if runway_days_cash_only >= 180:
        return "SAFE"
    if runway_days_cash_only >= 90:
        return "WARN"
    return "CRITICAL"


def liquidity_runway(book: FinanceBook) -> LiquidityResult:
    """Compute daily burn and runway using cash-only and liquid assets."""
    daily_burn = (book.total_monthly_outflows() - book.total_monthly_income()) / 30

    if daily_burn <= 0:
        return LiquidityResult(
            daily_burn=daily_burn,
            runway_days_cash_only=math.inf,
            runway_days_liquid_assets=math.inf,
            status="SAFE",
        )

    runway_days_cash_only = book.balance_sheet.cash / daily_burn
    runway_days_liquid_assets = book.liquid_assets() / daily_burn

    return LiquidityResult(
        daily_burn=daily_burn,
        runway_days_cash_only=runway_days_cash_only,
        runway_days_liquid_assets=runway_days_liquid_assets,
        status=_status_from_cash_runway(runway_days_cash_only),
    )

