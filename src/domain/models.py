"""Pydantic models to represent simple portfolio concepts."""

from decimal import Decimal

from pydantic import BaseModel, Field


class Position(BaseModel):
    name: str
    notional: Decimal = Field(gt=Decimal("0"), description="Position size in base currency.")
    tags: list[str] = Field(default_factory=list)

