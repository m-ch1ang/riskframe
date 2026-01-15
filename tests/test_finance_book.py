"""Tests for FinanceBook computed totals."""

import pytest

from src.config.defaults import load_default_book
from src.config.schema import (
    BalanceSheet,
    FinanceBook,
    FixedLiability,
    IncomeStream,
    VariableExposure,
)


class TestFinanceBookComputedTotals:
    """Test suite for FinanceBook computed property methods."""

    def test_total_monthly_income(self) -> None:
        """Income streams should sum correctly."""
        book = load_default_book()
        # Salary 8000 + Side Gig 1500 + Dividends 200 = 9700
        assert book.total_monthly_income() == pytest.approx(9700.0)

    def test_total_fixed_outflows(self) -> None:
        """Fixed liabilities should sum correctly."""
        book = load_default_book()
        # Rent 2500 + Insurance 350 + Subscriptions 150 = 3000
        assert book.total_fixed_outflows() == pytest.approx(3000.0)

    def test_total_variable_outflows(self) -> None:
        """Variable exposures should sum correctly."""
        book = load_default_book()
        # Groceries 600 + Utilities 200 + Entertainment 400 = 1200
        assert book.total_variable_outflows() == pytest.approx(1200.0)

    def test_total_monthly_outflows(self) -> None:
        """Total outflows should be fixed + variable."""
        book = load_default_book()
        # 3000 + 1200 = 4200
        assert book.total_monthly_outflows() == pytest.approx(4200.0)

    def test_liquid_assets(self) -> None:
        """Liquid assets should be cash + investments."""
        book = load_default_book()
        # Cash 15000 + Investments 50000 = 65000
        assert book.liquid_assets() == pytest.approx(65000.0)

    def test_net_liquid_worth(self) -> None:
        """Net liquid worth should be liquid assets - debt."""
        book = load_default_book()
        # 65000 - 25000 = 40000
        assert book.net_liquid_worth() == pytest.approx(40000.0)

    def test_monthly_net_cashflow(self) -> None:
        """Monthly net cashflow should be income - outflows."""
        book = load_default_book()
        # 9700 - 4200 = 5500
        assert book.monthly_net_cashflow() == pytest.approx(5500.0)


class TestFinanceBookWithCustomData:
    """Test FinanceBook with custom data to verify computation logic."""

    def test_empty_lists(self) -> None:
        """Empty income/liability lists should yield zero totals."""
        book = FinanceBook(
            balance_sheet=BalanceSheet(
                cash=1000.0,
                investments=2000.0,
                illiquid_assets=0.0,
                debt=500.0,
            ),
            income_streams=[],
            fixed_liabilities=[],
            variable_exposures=[],
        )
        assert book.total_monthly_income() == 0.0
        assert book.total_fixed_outflows() == 0.0
        assert book.total_variable_outflows() == 0.0
        assert book.total_monthly_outflows() == 0.0
        assert book.liquid_assets() == pytest.approx(3000.0)
        assert book.net_liquid_worth() == pytest.approx(2500.0)
        assert book.monthly_net_cashflow() == 0.0

    def test_single_income_stream(self) -> None:
        """Single income stream should return its value."""
        book = FinanceBook(
            balance_sheet=BalanceSheet(
                cash=100.0,
                investments=0.0,
                illiquid_assets=0.0,
                debt=0.0,
            ),
            income_streams=[IncomeStream(name="Job", monthly=5000.0)],
            fixed_liabilities=[],
            variable_exposures=[],
        )
        assert book.total_monthly_income() == pytest.approx(5000.0)

    def test_negative_cashflow(self) -> None:
        """Outflows exceeding income should yield negative cashflow."""
        book = FinanceBook(
            balance_sheet=BalanceSheet(
                cash=0.0,
                investments=0.0,
                illiquid_assets=0.0,
                debt=0.0,
            ),
            income_streams=[IncomeStream(name="Part-time", monthly=1000.0)],
            fixed_liabilities=[FixedLiability(name="Rent", monthly=2000.0)],
            variable_exposures=[],
        )
        assert book.monthly_net_cashflow() == pytest.approx(-1000.0)


class TestIncomeStreamValidation:
    """Test IncomeStream volatility validation."""

    def test_volatility_default(self) -> None:
        """Volatility should default to 0.0."""
        stream = IncomeStream(name="Test", monthly=100.0)
        assert stream.volatility == 0.0

    def test_volatility_in_range(self) -> None:
        """Volatility within 0-2 should be accepted."""
        stream = IncomeStream(name="Test", monthly=100.0, volatility=1.5)
        assert stream.volatility == 1.5

    def test_volatility_at_boundaries(self) -> None:
        """Volatility at 0 and 2 should be accepted."""
        stream_min = IncomeStream(name="Min", monthly=100.0, volatility=0.0)
        stream_max = IncomeStream(name="Max", monthly=100.0, volatility=2.0)
        assert stream_min.volatility == 0.0
        assert stream_max.volatility == 2.0

    def test_volatility_out_of_range_raises(self) -> None:
        """Volatility outside 0-2 should raise ValidationError."""
        with pytest.raises(Exception):
            IncomeStream(name="Invalid", monthly=100.0, volatility=2.5)
        with pytest.raises(Exception):
            IncomeStream(name="Invalid", monthly=100.0, volatility=-0.1)
