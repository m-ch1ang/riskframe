"""Pydantic models to represent simple portfolio concepts."""

from decimal import Decimal

from pydantic import BaseModel, Field

# Re-export finance models from schema for domain-level usage
from src.config.schema import (
    BalanceSheet,
    FinanceBook,
    FixedLiability,
    IncomeStream,
    VariableExposure,
)

__all__ = [
    "Position",
    "BalanceSheet",
    "IncomeStream",
    "FixedLiability",
    "VariableExposure",
    "FinanceBook",
]


class Position(BaseModel):
    name: str
    notional: Decimal = Field(gt=Decimal("0"), description="Position size in base currency.")
    tags: list[str] = Field(default_factory=list)
