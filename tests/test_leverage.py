import pytest

from src.config.schema import (
    BalanceSheet,
    FinanceBook,
    FixedLiability,
    IncomeStream,
    VariableExposure,
)
from src.risk.leverage import LeverageResult, leverage_metrics


def _book(
    cash: float = 5000.0,
    investments: float = 10000.0,
    debt: float = 2000.0,
    income: float = 5000.0,
    fixed: float = 2000.0,
    variable: float = 1000.0,
) -> FinanceBook:
    """Helper that builds a FinanceBook from scalar overrides."""
    return FinanceBook(
        balance_sheet=BalanceSheet(
            cash=cash,
            investments=investments,
            illiquid_assets=0.0,
            debt=debt,
        ),
        income_streams=[IncomeStream(name="Salary", monthly=income)] if income else [],
        fixed_liabilities=[FixedLiability(name="Rent", monthly=fixed)] if fixed else [],
        variable_exposures=[VariableExposure(name="Misc", monthly_avg=variable)],
    )


def test_normal_case() -> None:
    """All inputs positive; verify ratio values and no flags."""
    # cash=5000, investments=10000, debt=2000  -> net_liquid = 13000
    # income=5000, fixed=2000, variable=1000   -> outflows=3000
    book = _book()
    result = leverage_metrics(book)

    assert result.flags == []
    assert result.leverage_income_ratio == pytest.approx(3000.0 / 5000.0)
    assert result.leverage_net_liquid == pytest.approx(3000.0 / 13000.0)
    assert result.fixed_coverage_ratio == pytest.approx(5000.0 / 2000.0)


def test_zero_income() -> None:
    """When income is zero, leverage_income_ratio is None and income_zero is flagged."""
    book = _book(income=0.0)
    result = leverage_metrics(book)

    assert result.leverage_income_ratio is None
    assert "income_zero" in result.flags
    # fixed_coverage_ratio is also None since income/fixed would be 0/2000 = 0,
    # but income==0 means fixed_coverage_ratio = 0/2000 = 0.0 (not None)
    assert result.fixed_coverage_ratio == pytest.approx(0.0)
    assert result.leverage_net_liquid is not None


def test_zero_net_liquid() -> None:
    """When net liquid worth is exactly 0, clamp applies and flag is set."""
    # net_liquid = cash + investments - debt = 1000 + 1000 - 2000 = 0
    book = _book(cash=1000.0, investments=1000.0, debt=2000.0)
    result = leverage_metrics(book)

    assert "net_liquid_nonpositive" in result.flags
    # outflows = 2000 + 1000 = 3000; denominator clamped to 1e-9
    assert result.leverage_net_liquid == pytest.approx(3000.0 / 1e-9)


def test_negative_net_liquid() -> None:
    """When debt exceeds liquid assets, net_liquid is negative; flag is set."""
    # net_liquid = 500 + 500 - 5000 = -4000
    book = _book(cash=500.0, investments=500.0, debt=5000.0)
    result = leverage_metrics(book)

    assert "net_liquid_nonpositive" in result.flags
    # denominator clamped to 1e-9; result should be a large positive number
    assert result.leverage_net_liquid == pytest.approx(3000.0 / 1e-9)


def test_zero_fixed_outflows() -> None:
    """When there are no fixed liabilities, fixed_coverage_ratio is None and flagged."""
    book = _book(fixed=0.0)
    result = leverage_metrics(book)

    assert result.fixed_coverage_ratio is None
    assert "fixed_outflows_zero" in result.flags
    # outflows = 0 + 1000 = 1000 (variable only)
    assert result.leverage_income_ratio == pytest.approx(1000.0 / 5000.0)


def test_all_edge_cases() -> None:
    """income=0, net_liquid<=0, and fixed_outflows=0 all at once: all three flags raised."""
    book = FinanceBook(
        balance_sheet=BalanceSheet(
            cash=0.0,
            investments=0.0,
            illiquid_assets=0.0,
            debt=1000.0,
        ),
        income_streams=[],
        fixed_liabilities=[],
        variable_exposures=[VariableExposure(name="Misc", monthly_avg=500.0)],
    )
    result = leverage_metrics(book)

    assert "income_zero" in result.flags
    assert "net_liquid_nonpositive" in result.flags
    assert "fixed_outflows_zero" in result.flags
    assert result.leverage_income_ratio is None
    assert result.fixed_coverage_ratio is None
    assert result.leverage_net_liquid == pytest.approx(500.0 / 1e-9)


def test_return_type() -> None:
    """leverage_metrics always returns a LeverageResult instance."""
    assert isinstance(leverage_metrics(_book()), LeverageResult)
