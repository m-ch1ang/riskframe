import math

import pytest

from src.config.schema import (
    BalanceSheet,
    FinanceBook,
    FixedLiability,
    IncomeStream,
    VariableExposure,
)
from src.risk.liquidity import liquidity_runway


def test_liquidity_runway_positive_burn() -> None:
    """When outflows exceed income, runway should be finite."""
    book = FinanceBook(
        balance_sheet=BalanceSheet(
            cash=1000.0,
            investments=500.0,
            illiquid_assets=0.0,
            debt=0.0,
        ),
        income_streams=[IncomeStream(name="Income", monthly=1000.0)],
        fixed_liabilities=[FixedLiability(name="Rent", monthly=1800.0)],
        variable_exposures=[VariableExposure(name="Spend", monthly_avg=200.0)],
    )

    result = liquidity_runway(book)
    # Burn = (2000 - 1000) / 30 = 33.333...
    assert result.daily_burn == pytest.approx(1000.0 / 30.0)
    assert result.runway_days_cash_only == pytest.approx(30.0)
    assert result.runway_days_liquid_assets == pytest.approx(45.0)
    assert result.status == "CRITICAL"


def test_liquidity_runway_negative_burn_is_infinite() -> None:
    """When income covers outflows, runway should be infinite."""
    book = FinanceBook(
        balance_sheet=BalanceSheet(
            cash=2500.0,
            investments=7000.0,
            illiquid_assets=0.0,
            debt=0.0,
        ),
        income_streams=[IncomeStream(name="Income", monthly=3000.0)],
        fixed_liabilities=[FixedLiability(name="Rent", monthly=1500.0)],
        variable_exposures=[VariableExposure(name="Spend", monthly_avg=500.0)],
    )

    result = liquidity_runway(book)
    assert result.daily_burn == pytest.approx(-1000.0 / 30.0)
    assert math.isinf(result.runway_days_cash_only)
    assert math.isinf(result.runway_days_liquid_assets)
    assert result.status == "SAFE"


def test_liquidity_runway_zero_cash_edge_case() -> None:
    """Cash-only runway should be zero when cash is zero and burn is positive."""
    book = FinanceBook(
        balance_sheet=BalanceSheet(
            cash=0.0,
            investments=900.0,
            illiquid_assets=0.0,
            debt=0.0,
        ),
        income_streams=[IncomeStream(name="Income", monthly=1000.0)],
        fixed_liabilities=[FixedLiability(name="Rent", monthly=1600.0)],
        variable_exposures=[VariableExposure(name="Spend", monthly_avg=200.0)],
    )

    result = liquidity_runway(book)
    # Burn = (1800 - 1000) / 30 = 26.666...
    assert result.daily_burn == pytest.approx(800.0 / 30.0)
    assert result.runway_days_cash_only == pytest.approx(0.0)
    assert result.runway_days_liquid_assets == pytest.approx(33.75)
    assert result.status == "CRITICAL"

