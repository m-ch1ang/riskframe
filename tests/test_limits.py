import pytest

from src.config.schema import BalanceSheet, FinanceBook, FixedLiability, IncomeStream
from src.risk.limits import max_safe_spend_today


def _book(cash: float, monthly_income: float, monthly_outflows: float) -> FinanceBook:
    return FinanceBook(
        balance_sheet=BalanceSheet(
            cash=cash,
            investments=0.0,
            illiquid_assets=0.0,
            debt=0.0,
        ),
        income_streams=[IncomeStream(name="salary", monthly=monthly_income)],
        fixed_liabilities=[FixedLiability(name="expenses", monthly=monthly_outflows)],
    )


def test_burn_positive_enough_cash():
    # daily_burn = (9000 - 6000) / 30 = 100
    # required_buffer = 42 * 100 = 4200
    # max_safe_spend = 10000 - 4200 = 5800
    book = _book(cash=10_000, monthly_income=6_000, monthly_outflows=9_000)
    result = max_safe_spend_today(book, min_runway_days=42, use_cash_only=True)

    assert result.basis == "CASH_ONLY"
    assert result.min_runway_days == 42
    assert result.required_buffer == pytest.approx(4_200.0)
    assert result.max_safe_spend == pytest.approx(5_800.0)


def test_burn_positive_low_cash_returns_zero():
    # daily_burn = 100, required_buffer = 4200, cash = 3000 → clamped to 0
    book = _book(cash=3_000, monthly_income=6_000, monthly_outflows=9_000)
    result = max_safe_spend_today(book, min_runway_days=42, use_cash_only=True)

    assert result.required_buffer == pytest.approx(4_200.0)
    assert result.max_safe_spend == pytest.approx(0.0)


def test_burn_negative_returns_full_cash():
    # income > outflows → daily_burn <= 0 → max_safe_spend = cash
    book = _book(cash=8_000, monthly_income=7_000, monthly_outflows=4_000)
    result = max_safe_spend_today(book, min_runway_days=42, use_cash_only=True)

    assert result.required_buffer == pytest.approx(0.0)
    assert result.max_safe_spend == pytest.approx(8_000.0)
    assert result.basis == "CASH_ONLY"
