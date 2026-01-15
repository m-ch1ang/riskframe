"""Pydantic schemas for application configuration."""

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    base_currency: str = Field(default="USD", description="ISO currency code for reporting.")

