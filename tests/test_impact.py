import math

import pytest

from src.config.schema import BalanceSheet, FinanceBook, FixedLiability, IncomeStream
from src.risk.impact import PurchaseImpactResult, evaluate_purchase


def _book(
    cash: float,
    debt: float,
    monthly_income: float,
    monthly_outflows: float,
) -> FinanceBook:
    return FinanceBook(
        balance_sheet=BalanceSheet(
            cash=cash,
            investments=0.0,
            illiquid_assets=0.0,
            debt=debt,
        ),
        income_streams=[IncomeStream(name="salary", monthly=monthly_income)],
        fixed_liabilities=[FixedLiability(name="expenses", monthly=monthly_outflows)],
    )


class TestPurchaseWithinCash:
    """Purchase amount is fully covered by existing cash."""

    def test_debt_financed_is_zero(self):
        # cash=10_000 > purchase=3_000
        book = _book(cash=10_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=3_000, min_runway_days=42)

        assert result.debt_financed == pytest.approx(0.0)

    def test_pre_snapshot(self):
        # daily_burn = (9000 - 6000) / 30 = 100
        # pre runway = 10_000 / 100 = 100 days
        # pre max_safe_spend = 10_000 - 42*100 = 5_800
        book = _book(cash=10_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=3_000, min_runway_days=42)

        assert result.pre.runway_days_cash_only == pytest.approx(100.0)
        assert result.pre.leverage_income_ratio == pytest.approx(9_000 / 6_000)
        assert result.pre.max_safe_spend_today == pytest.approx(5_800.0)

    def test_post_snapshot(self):
        # post cash = 10_000 - 3_000 = 7_000
        # post runway = 7_000 / 100 = 70 days
        # post max_safe_spend = 7_000 - 4_200 = 2_800
        book = _book(cash=10_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=3_000, min_runway_days=42)

        assert result.post.runway_days_cash_only == pytest.approx(70.0)
        assert result.post.leverage_income_ratio == pytest.approx(9_000 / 6_000)
        assert result.post.max_safe_spend_today == pytest.approx(2_800.0)

    def test_deltas(self):
        book = _book(cash=10_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=3_000, min_runway_days=42)

        assert result.delta_runway_days == pytest.approx(-30.0)
        assert result.delta_leverage_income_ratio == pytest.approx(0.0)
        assert result.delta_max_safe_spend == pytest.approx(-3_000.0)

    def test_return_type(self):
        book = _book(cash=10_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        assert isinstance(evaluate_purchase(book, 3_000), PurchaseImpactResult)


class TestPurchaseBeyondCash:
    """Purchase amount exceeds cash; shortfall is modelled as new debt."""

    def test_debt_financed_equals_shortfall(self):
        # cash=2_000, purchase=5_000 → debt_financed = 3_000
        book = _book(cash=2_000, debt=1_000, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        assert result.debt_financed == pytest.approx(3_000.0)

    def test_post_cash_is_zero(self):
        book = _book(cash=2_000, debt=1_000, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        # Cash must be fully exhausted
        assert result.post.runway_days_cash_only == pytest.approx(0.0)

    def test_post_runway_reflects_zero_cash(self):
        # daily_burn = 100; post cash = 0 → runway = 0
        book = _book(cash=2_000, debt=1_000, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        assert result.post.runway_days_cash_only == pytest.approx(0.0)

    def test_pre_runway_uses_original_cash(self):
        # pre runway = 2_000 / 100 = 20 days
        book = _book(cash=2_000, debt=1_000, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        assert result.pre.runway_days_cash_only == pytest.approx(20.0)

    def test_delta_runway_negative(self):
        book = _book(cash=2_000, debt=1_000, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        assert result.delta_runway_days == pytest.approx(-20.0)

    def test_purchase_amount_stored(self):
        book = _book(cash=2_000, debt=1_000, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=5_000)

        assert result.purchase_amount == pytest.approx(5_000.0)


class TestExactCashEdgeCase:
    """Purchase amount equals cash exactly — no debt, cash goes to zero."""

    def test_no_debt_financed(self):
        book = _book(cash=5_000, debt=0, monthly_income=3_000, monthly_outflows=4_500)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        assert result.debt_financed == pytest.approx(0.0)

    def test_post_runway_is_zero(self):
        # daily_burn = (4500 - 3000) / 30 = 50; post cash = 0
        book = _book(cash=5_000, debt=0, monthly_income=3_000, monthly_outflows=4_500)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        assert result.post.runway_days_cash_only == pytest.approx(0.0)

    def test_delta_runway(self):
        # pre runway = 5_000 / 50 = 100; post runway = 0 → delta = -100
        book = _book(cash=5_000, debt=0, monthly_income=3_000, monthly_outflows=4_500)
        result = evaluate_purchase(book, purchase_amount=5_000, min_runway_days=42)

        assert result.delta_runway_days == pytest.approx(-100.0)


class TestMessageBreachWarning:
    """Message includes a breach warning when post-runway < min_runway_days."""

    def test_message_contains_breach_language(self):
        # daily_burn = 100; purchase 4_000 → post cash 1_000 → runway 10 < 42
        book = _book(cash=5_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=4_000, min_runway_days=42)

        assert result.post.runway_days_cash_only == pytest.approx(10.0)
        assert "breaches" in result.message.lower()
        assert "42" in result.message

    def test_message_includes_post_runway_value(self):
        book = _book(cash=5_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=4_000, min_runway_days=42)

        assert "10.0" in result.message


class TestMessageSafe:
    """Message does not warn about a breach when post-runway is comfortably above threshold."""

    def test_no_breach_language_when_safe(self):
        # daily_burn = 100; purchase 1_000 → post cash 49_000 → runway 490 > 42
        book = _book(cash=50_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=1_000, min_runway_days=42)

        assert result.post.runway_days_cash_only == pytest.approx(490.0)
        assert "breaches" not in result.message.lower()

    def test_message_contains_post_runway_value(self):
        book = _book(cash=50_000, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=1_000, min_runway_days=42)

        assert "490.0" in result.message

    def test_message_contains_debt_note_when_debt_financed(self):
        # Debt-financed purchase should mention debt amount in message
        book = _book(cash=500, debt=0, monthly_income=6_000, monthly_outflows=9_000)
        result = evaluate_purchase(book, purchase_amount=1_500, min_runway_days=42)

        assert result.debt_financed == pytest.approx(1_000.0)
        assert "debt" in result.message.lower()
