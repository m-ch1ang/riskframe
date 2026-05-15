"""Deterministic tests for stress scenario functions.

Shared fixture
--------------
cash=6_000, income=3_000/mo, fixed outflows=4_500/mo
  baseline daily_burn = (4_500 - 3_000) / 30 = 50 $/day
  baseline runway     = 6_000 / 50 = 120 days
"""

import math

import pytest

from src.config.schema import BalanceSheet, FinanceBook, FixedLiability, IncomeStream
from src.risk.stress import (
    StressTestResult,
    stress_income_delay,
    stress_income_drop,
    stress_one_time_shock,
)


def _book(
    cash: float = 6_000,
    income: float = 3_000,
    outflows: float = 4_500,
    debt: float = 0,
) -> FinanceBook:
    return FinanceBook(
        balance_sheet=BalanceSheet(
            cash=cash,
            investments=0.0,
            illiquid_assets=0.0,
            debt=debt,
        ),
        income_streams=[IncomeStream(name="salary", monthly=income)],
        fixed_liabilities=[FixedLiability(name="expenses", monthly=outflows)],
    )


# ---------------------------------------------------------------------------
# Scenario A – income_drop
# ---------------------------------------------------------------------------


class TestIncomeDrop:
    """stress_income_drop reduces all income streams by pct_drop."""

    def test_return_type(self):
        assert isinstance(stress_income_drop(_book(), pct_drop=0.5), StressTestResult)

    def test_scenario_name(self):
        result = stress_income_drop(_book(), pct_drop=0.5)
        assert result.scenario_name == "income_drop"

    def test_parameters_stored(self):
        result = stress_income_drop(_book(), pct_drop=0.3)
        assert result.parameters == {"pct_drop": 0.3}

    def test_50pct_drop_runway(self):
        # reduced_income=1_500, daily_burn=(4_500-1_500)/30=100, runway=6_000/100=60
        result = stress_income_drop(_book(), pct_drop=0.5)
        assert result.runway_days == pytest.approx(60.0)

    def test_50pct_drop_months(self):
        # ceil(60/30) = 2
        result = stress_income_drop(_book(), pct_drop=0.5)
        assert result.months_to_insolvency == pytest.approx(2.0)

    def test_50pct_drop_fails_default_buffer(self):
        # 60 < 90
        result = stress_income_drop(_book(), pct_drop=0.5)
        assert result.status == "FAIL"

    def test_20pct_drop_runway(self):
        # reduced_income=2_400, daily_burn=(4_500-2_400)/30=70, runway=6_000/70≈85.71
        result = stress_income_drop(_book(), pct_drop=0.2)
        assert result.runway_days == pytest.approx(6_000 / 70.0)

    def test_20pct_drop_months(self):
        # ceil(85.71/30) = ceil(2.857) = 3
        result = stress_income_drop(_book(), pct_drop=0.2)
        assert result.months_to_insolvency == pytest.approx(3.0)

    def test_100pct_drop_runway(self):
        # No income at all; daily_burn=4_500/30=150; runway=6_000/150=40
        result = stress_income_drop(_book(), pct_drop=1.0)
        assert result.runway_days == pytest.approx(40.0)

    def test_100pct_drop_months(self):
        # ceil(40/30) = 2
        result = stress_income_drop(_book(), pct_drop=1.0)
        assert result.months_to_insolvency == pytest.approx(2.0)

    def test_pass_when_runway_meets_buffer(self):
        # buffer_days=50; runway=60 >= 50 → PASS
        result = stress_income_drop(_book(), pct_drop=0.5, buffer_days=50)
        assert result.status == "PASS"

    def test_zero_drop_is_baseline_runway(self):
        # No reduction; baseline burn=50; runway=120
        result = stress_income_drop(_book(), pct_drop=0.0)
        assert result.runway_days == pytest.approx(120.0)

    def test_negative_burn_gives_infinite_runway(self):
        # income=5_000 > outflows=4_500 even after 20% drop (4_000 > 4_500 is false);
        # use a drop so small burn stays negative: income=6_000 * 0.1 drop=5_400 > 4_500
        book = _book(income=6_000, outflows=4_500)
        result = stress_income_drop(book, pct_drop=0.1)
        # reduced_income=5_400, daily_burn=(4_500-5_400)/30 < 0 → inf
        assert math.isinf(result.runway_days)
        assert math.isinf(result.months_to_insolvency)
        assert result.status == "PASS"


# ---------------------------------------------------------------------------
# Scenario B – income_delay
# ---------------------------------------------------------------------------


class TestIncomeDelay:
    """stress_income_delay zeroes income for delay_months, then resumes."""

    def test_return_type(self):
        assert isinstance(stress_income_delay(_book(), delay_months=1), StressTestResult)

    def test_scenario_name(self):
        result = stress_income_delay(_book(), delay_months=1)
        assert result.scenario_name == "income_delay"

    def test_parameters_stored(self):
        result = stress_income_delay(_book(), delay_months=2)
        assert result.parameters == {"delay_months": 2}

    def test_1month_delay_runway(self):
        # Phase 1: burn_p1=4_500/30=150, phase1_days=30, cash_after=6_000-4_500=1_500
        # Phase 2: burn_p2=50, additional=1_500/50=30 → total=30+30=60
        result = stress_income_delay(_book(), delay_months=1)
        assert result.runway_days == pytest.approx(60.0)

    def test_1month_delay_months(self):
        # ceil(60/30) = 2
        result = stress_income_delay(_book(), delay_months=1)
        assert result.months_to_insolvency == pytest.approx(2.0)

    def test_1month_delay_fails_default_buffer(self):
        result = stress_income_delay(_book(), delay_months=1)
        assert result.status == "FAIL"

    def test_insolvent_during_delay(self):
        # cash=2_000, outflows=4_500 → burn_p1=150, phase1_runway=2_000/150≈13.33 < 30
        result = stress_income_delay(_book(cash=2_000), delay_months=1)
        assert result.runway_days == pytest.approx(2_000 / 150.0)

    def test_insolvent_during_delay_months(self):
        # ceil(13.33/30) = ceil(0.444) = 1
        result = stress_income_delay(_book(cash=2_000), delay_months=1)
        assert result.months_to_insolvency == pytest.approx(1.0)

    def test_phase2_negative_burn_gives_infinite_runway(self):
        # income=6_000, outflows=4_500 → phase2 burn=(4_500-6_000)/30 < 0
        # Cash is sufficient to survive phase 1
        book = _book(cash=10_000, income=6_000, outflows=4_500)
        result = stress_income_delay(book, delay_months=1)
        # phase1: burn=150, cash_after=10_000-4_500=5_500 > 0; phase2 burn < 0 → inf
        assert math.isinf(result.runway_days)
        assert result.status == "PASS"

    def test_pass_when_runway_meets_buffer(self):
        result = stress_income_delay(_book(), delay_months=1, buffer_days=60)
        assert result.status == "PASS"


# ---------------------------------------------------------------------------
# Scenario C – one_time_shock
# ---------------------------------------------------------------------------


class TestOneTimeShock:
    """stress_one_time_shock deducts a lump-sum expense from cash immediately."""

    def test_return_type(self):
        assert isinstance(stress_one_time_shock(_book(), shock_amount=1_000), StressTestResult)

    def test_scenario_name(self):
        result = stress_one_time_shock(_book(), shock_amount=5_000)
        assert result.scenario_name == "one_time_shock"

    def test_parameters_stored(self):
        result = stress_one_time_shock(_book(), shock_amount=5_000)
        assert result.parameters == {"shock_amount": 5_000}

    def test_shock_within_cash_runway(self):
        # effective_cash=6_000-5_000=1_000; daily_burn=50; runway=20
        result = stress_one_time_shock(_book(), shock_amount=5_000)
        assert result.runway_days == pytest.approx(20.0)

    def test_shock_within_cash_months(self):
        # ceil(20/30) = 1
        result = stress_one_time_shock(_book(), shock_amount=5_000)
        assert result.months_to_insolvency == pytest.approx(1.0)

    def test_shock_within_cash_fails_default_buffer(self):
        result = stress_one_time_shock(_book(), shock_amount=5_000)
        assert result.status == "FAIL"

    def test_shock_beyond_cash_runway_is_zero(self):
        # shock=8_000 > cash=6_000 → effective_cash=0; runway=0
        result = stress_one_time_shock(_book(), shock_amount=8_000)
        assert result.runway_days == pytest.approx(0.0)

    def test_shock_beyond_cash_months_is_zero(self):
        # ceil(0/30) = 0
        result = stress_one_time_shock(_book(), shock_amount=8_000)
        assert result.months_to_insolvency == pytest.approx(0.0)

    def test_shock_exact_cash_runway_is_zero(self):
        # shock == cash → effective_cash=0
        result = stress_one_time_shock(_book(), shock_amount=6_000)
        assert result.runway_days == pytest.approx(0.0)

    def test_shock_with_no_burn_infinite_runway(self):
        # income=6_000 > outflows=4_500 → daily_burn < 0 → runway = inf despite shock
        book = _book(cash=6_000, income=6_000, outflows=4_500)
        result = stress_one_time_shock(book, shock_amount=3_000)
        assert math.isinf(result.runway_days)
        assert result.status == "PASS"

    def test_pass_when_runway_meets_buffer(self):
        # effective_cash=5_500, daily_burn=50, runway=110 >= 90
        result = stress_one_time_shock(_book(), shock_amount=500, buffer_days=90)
        assert result.status == "PASS"
