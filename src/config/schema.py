"""Pydantic schemas for application configuration."""

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    base_currency: str = Field(default="USD", description="ISO currency code for reporting.")


class BalanceSheet(BaseModel):
    """Snapshot of assets and liabilities."""

    cash: float = Field(description="Liquid cash holdings.")
    investments: float = Field(description="Marketable securities and investment accounts.")
    illiquid_assets: float = Field(description="Real estate, private holdings, etc.")
    debt: float = Field(description="Total outstanding debt.")


class IncomeStream(BaseModel):
    """A recurring income source."""

    name: str = Field(description="Descriptive name of the income stream.")
    monthly: float = Field(description="Expected monthly income amount.")
    volatility: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Income volatility factor (0 = stable, up to 2 = highly variable).",
    )


class FixedLiability(BaseModel):
    """A fixed recurring expense."""

    name: str = Field(description="Descriptive name of the liability.")
    monthly: float = Field(description="Fixed monthly payment amount.")


class VariableExposure(BaseModel):
    """A variable recurring expense."""

    name: str = Field(description="Descriptive name of the variable expense.")
    monthly_avg: float = Field(description="Average monthly amount for this expense.")


class FinanceBook(BaseModel):
    """Container aggregating personal finance data."""

    balance_sheet: BalanceSheet
    income_streams: list[IncomeStream] = Field(default_factory=list)
    fixed_liabilities: list[FixedLiability] = Field(default_factory=list)
    variable_exposures: list[VariableExposure] = Field(default_factory=list)

    def total_monthly_income(self) -> float:
        """Sum of all income streams."""
        return sum(stream.monthly for stream in self.income_streams)

    def total_fixed_outflows(self) -> float:
        """Sum of all fixed liabilities."""
        return sum(liability.monthly for liability in self.fixed_liabilities)

    def total_variable_outflows(self) -> float:
        """Sum of average variable exposures."""
        return sum(exposure.monthly_avg for exposure in self.variable_exposures)

    def total_monthly_outflows(self) -> float:
        """Total of fixed and variable outflows."""
        return self.total_fixed_outflows() + self.total_variable_outflows()

    def liquid_assets(self) -> float:
        """Cash plus investments."""
        return self.balance_sheet.cash + self.balance_sheet.investments

    def net_liquid_worth(self) -> float:
        """Liquid assets minus debt."""
        return self.liquid_assets() - self.balance_sheet.debt

    def monthly_net_cashflow(self) -> float:
        """Monthly income minus total outflows."""
        return self.total_monthly_income() - self.total_monthly_outflows()
