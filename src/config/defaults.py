"""Application-level defaults."""

from src.config.schema import (
    BalanceSheet,
    FinanceBook,
    FixedLiability,
    IncomeStream,
    VariableExposure,
)

APP_NAME = "Riskframe"
APP_DESCRIPTION = "Local-first desk for treating personal finance like a trading book."
BASE_CURRENCY = "USD"

# Sample default data
DEFAULT_BALANCE_SHEET = BalanceSheet(
    cash=15000.0,
    investments=50000.0,
    illiquid_assets=200000.0,
    debt=25000.0,
)

DEFAULT_INCOME_STREAMS = [
    IncomeStream(name="Salary", monthly=8000.0, volatility=0.0),
    IncomeStream(name="Side Gig", monthly=1500.0, volatility=0.8),
    IncomeStream(name="Dividends", monthly=200.0, volatility=0.3),
]

DEFAULT_FIXED_LIABILITIES = [
    FixedLiability(name="Rent", monthly=2500.0),
    FixedLiability(name="Insurance", monthly=350.0),
    FixedLiability(name="Subscriptions", monthly=150.0),
]

DEFAULT_VARIABLE_EXPOSURES = [
    VariableExposure(name="Groceries", monthly_avg=600.0),
    VariableExposure(name="Utilities", monthly_avg=200.0),
    VariableExposure(name="Entertainment", monthly_avg=400.0),
]


def load_default_book() -> FinanceBook:
    """Return a FinanceBook populated with sample default data."""
    return FinanceBook(
        balance_sheet=DEFAULT_BALANCE_SHEET,
        income_streams=DEFAULT_INCOME_STREAMS,
        fixed_liabilities=DEFAULT_FIXED_LIABILITIES,
        variable_exposures=DEFAULT_VARIABLE_EXPOSURES,
    )
