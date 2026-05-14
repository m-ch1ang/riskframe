"""Purchase impact analysis.

Models the effect of a one-time purchase on liquidity, leverage, and spending
headroom.  When ``purchase_amount`` exceeds available cash the shortfall is
treated as additional debt (leverage path) rather than rejected, which mirrors
how a credit-financed purchase works in practice.
"""

import math
from dataclasses import dataclass
from typing import Optional

from src.config.schema import FinanceBook
from src.risk.leverage import leverage_metrics
from src.risk.limits import max_safe_spend_today
from src.risk.liquidity import liquidity_runway


@dataclass
class PurchaseSnapshot:
    """Key risk metrics captured at a single point in time."""

    runway_days_cash_only: float
    leverage_income_ratio: Optional[float]
    max_safe_spend_today: float


@dataclass
class PurchaseImpactResult:
    """Full before/after risk picture for a prospective purchase.

    Attributes
    ----------
    purchase_amount:
        The nominal size of the purchase being evaluated.
    debt_financed:
        The portion funded by new debt (0 when cash covers the full amount).
        When ``purchase_amount > cash``, ``debt_financed = purchase_amount - cash``
        and cash is set to zero on the post-purchase book.
    pre:
        Risk snapshot computed from the unmodified ``FinanceBook``.
    post:
        Risk snapshot computed after applying the purchase to the book.
    delta_runway_days:
        ``post.runway_days_cash_only - pre.runway_days_cash_only``.
        Negative values indicate a reduction in runway.
    delta_leverage_income_ratio:
        Change in outflows-to-income leverage.  ``None`` when income is zero
        both before and after (ratio is undefined in that state).
    delta_max_safe_spend:
        Change in the maximum safe discretionary spend.
    message:
        Human-readable risk-desk assessment of the purchase.
    """

    purchase_amount: float
    debt_financed: float
    pre: PurchaseSnapshot
    post: PurchaseSnapshot
    delta_runway_days: float
    delta_leverage_income_ratio: Optional[float]
    delta_max_safe_spend: float
    message: str


def _snapshot(book: FinanceBook, min_runway_days: int) -> PurchaseSnapshot:
    liq = liquidity_runway(book)
    lev = leverage_metrics(book)
    lim = max_safe_spend_today(book, min_runway_days=min_runway_days)
    return PurchaseSnapshot(
        runway_days_cash_only=liq.runway_days_cash_only,
        leverage_income_ratio=lev.leverage_income_ratio,
        max_safe_spend_today=lim.max_safe_spend,
    )


def _build_message(
    result_pre: PurchaseSnapshot,
    result_post: PurchaseSnapshot,
    purchase_amount: float,
    debt_financed: float,
    min_runway_days: int,
) -> str:
    runway = result_post.runway_days_cash_only
    runway_str = f"{runway:.1f}" if math.isfinite(runway) else "∞"

    lev = result_post.leverage_income_ratio
    lev_str = f"{lev:.2f}" if lev is not None else "N/A"

    direction = "drops to" if runway < result_pre.runway_days_cash_only else "remains at"
    parts = [
        f"After this purchase, runway {direction} {runway_str} days"
        f" and leverage is {lev_str}."
    ]

    if math.isfinite(runway) and runway < min_runway_days:
        parts.append(
            f"This breaches your {min_runway_days}-day liquidity buffer."
        )

    if debt_financed > 0:
        parts.append(f"${debt_financed:,.2f} of this purchase is financed via debt.")

    return "  ".join(parts)


def evaluate_purchase(
    book: FinanceBook,
    purchase_amount: float,
    min_runway_days: int = 42,
) -> PurchaseImpactResult:
    """Evaluate the risk impact of a one-time purchase.

    Parameters
    ----------
    book:
        The current financial state.
    purchase_amount:
        The cost of the prospective purchase (must be >= 0).
    min_runway_days:
        Minimum cash runway threshold used for limit calculations and the
        breach warning in the generated message.  Defaults to 42 days.

    Returns
    -------
    PurchaseImpactResult
        Pre/post snapshots, deltas, and a human-readable risk message.

    Notes
    -----
    When ``purchase_amount > book.balance_sheet.cash`` the shortfall is
    modelled as new debt rather than rejected.  Cash is set to zero and
    ``debt`` is increased by the overage.  This mirrors a credit-financed
    purchase and keeps the analysis continuous across the cash boundary.
    """
    cash = book.balance_sheet.cash

    if purchase_amount <= cash:
        new_cash = cash - purchase_amount
        debt_financed = 0.0
    else:
        new_cash = 0.0
        debt_financed = purchase_amount - cash

    new_balance_sheet = book.balance_sheet.model_copy(
        update={
            "cash": new_cash,
            "debt": book.balance_sheet.debt + debt_financed,
        }
    )
    post_book = book.model_copy(update={"balance_sheet": new_balance_sheet})

    pre = _snapshot(book, min_runway_days)
    post = _snapshot(post_book, min_runway_days)

    if pre.leverage_income_ratio is not None and post.leverage_income_ratio is not None:
        delta_leverage: Optional[float] = (
            post.leverage_income_ratio - pre.leverage_income_ratio
        )
    else:
        delta_leverage = None

    message = _build_message(pre, post, purchase_amount, debt_financed, min_runway_days)

    return PurchaseImpactResult(
        purchase_amount=purchase_amount,
        debt_financed=debt_financed,
        pre=pre,
        post=post,
        delta_runway_days=post.runway_days_cash_only - pre.runway_days_cash_only,
        delta_leverage_income_ratio=delta_leverage,
        delta_max_safe_spend=post.max_safe_spend_today - pre.max_safe_spend_today,
        message=message,
    )
