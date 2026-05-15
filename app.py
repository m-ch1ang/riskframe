"""Riskframe — personal risk desk Streamlit application."""

import math

import pandas as pd
import streamlit as st

from src.charts.charts import (
    purchase_comparison_chart,
    runway_gauge,
    stress_comparison_chart,
)
from src.config.defaults import (
    APP_DESCRIPTION,
    APP_NAME,
    DEFAULT_BALANCE_SHEET,
    DEFAULT_FIXED_LIABILITIES,
    DEFAULT_INCOME_STREAMS,
    DEFAULT_VARIABLE_EXPOSURES,
)
from src.config.schema import (
    BalanceSheet,
    FinanceBook,
    FixedLiability,
    IncomeStream,
    VariableExposure,
)
from src.risk import (
    LeverageResult,
    LimitsResult,
    LiquidityResult,
    evaluate_purchase,
    leverage_metrics,
    liquidity_runway,
    max_safe_spend_today,
)
from src.risk.stress import (
    stress_income_delay,
    stress_income_drop,
    stress_one_time_shock,
)
from src.utils.money import format_currency

BASE_CURRENCY = "USD"
_INF_LABEL = "∞"


# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------


def _init_state() -> None:
    """Seed session state with default values on first load."""
    if "income_streams" not in st.session_state:
        st.session_state.income_streams = [
            {"name": s.name, "monthly": s.monthly, "volatility": s.volatility}
            for s in DEFAULT_INCOME_STREAMS
        ]
    if "fixed_liabilities" not in st.session_state:
        st.session_state.fixed_liabilities = [
            {"name": l.name, "monthly": l.monthly}
            for l in DEFAULT_FIXED_LIABILITIES
        ]
    if "variable_exposures" not in st.session_state:
        st.session_state.variable_exposures = [
            {"name": e.name, "monthly_avg": e.monthly_avg}
            for e in DEFAULT_VARIABLE_EXPOSURES
        ]
    if "cash" not in st.session_state:
        st.session_state.cash = DEFAULT_BALANCE_SHEET.cash
    if "investments" not in st.session_state:
        st.session_state.investments = DEFAULT_BALANCE_SHEET.investments
    if "debt" not in st.session_state:
        st.session_state.debt = DEFAULT_BALANCE_SHEET.debt
    if "buffer_days" not in st.session_state:
        st.session_state.buffer_days = 42


# ---------------------------------------------------------------------------
# FinanceBook assembly
# ---------------------------------------------------------------------------


def _build_book() -> FinanceBook:
    """Construct a FinanceBook from current session state."""
    balance_sheet = BalanceSheet(
        cash=st.session_state.cash,
        investments=st.session_state.investments,
        illiquid_assets=0.0,
        debt=st.session_state.debt,
    )
    income_streams = [
        IncomeStream(
            name=s["name"] or "Income",
            monthly=max(0.0, s["monthly"]),
            volatility=s["volatility"],
        )
        for s in st.session_state.income_streams
    ]
    fixed_liabilities = [
        FixedLiability(name=l["name"] or "Liability", monthly=max(0.0, l["monthly"]))
        for l in st.session_state.fixed_liabilities
    ]
    variable_exposures = [
        VariableExposure(
            name=e["name"] or "Exposure", monthly_avg=max(0.0, e["monthly_avg"])
        )
        for e in st.session_state.variable_exposures
    ]
    return FinanceBook(
        balance_sheet=balance_sheet,
        income_streams=income_streams,
        fixed_liabilities=fixed_liabilities,
        variable_exposures=variable_exposures,
    )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


def _render_sidebar() -> None:
    """Render all sidebar controls that drive the FinanceBook."""
    with st.sidebar:
        st.title(APP_NAME)
        st.caption(APP_DESCRIPTION)

        # ── Balance Sheet ──────────────────────────────────────────────────
        st.subheader("Balance Sheet")
        st.session_state.cash = st.number_input(
            "Cash ($)",
            min_value=0.0,
            value=float(st.session_state.cash),
            step=500.0,
            format="%.2f",
            key="_cash_input",
        )
        st.session_state.investments = st.number_input(
            "Investments ($)",
            min_value=0.0,
            value=float(st.session_state.investments),
            step=1000.0,
            format="%.2f",
            key="_inv_input",
        )
        st.session_state.debt = st.number_input(
            "Total Debt ($)",
            min_value=0.0,
            value=float(st.session_state.debt),
            step=500.0,
            format="%.2f",
            key="_debt_input",
        )

        # ── Income Streams ─────────────────────────────────────────────────
        st.divider()
        st.subheader("Income Streams")
        streams = st.session_state.income_streams
        remove_income_idx = None
        for i, stream in enumerate(streams):
            with st.expander(stream["name"] or f"Stream {i + 1}", expanded=False):
                stream["name"] = st.text_input(
                    "Name", value=stream["name"], key=f"inc_name_{i}"
                )
                stream["monthly"] = st.number_input(
                    "Monthly ($)",
                    min_value=0.0,
                    value=float(stream["monthly"]),
                    step=100.0,
                    format="%.2f",
                    key=f"inc_monthly_{i}",
                )
                stream["volatility"] = st.slider(
                    "Volatility",
                    min_value=0.0,
                    max_value=2.0,
                    value=float(stream["volatility"]),
                    step=0.05,
                    help="0 = stable, 2 = highly variable",
                    key=f"inc_vol_{i}",
                )
                if st.button("Remove", key=f"inc_rm_{i}", type="secondary"):
                    remove_income_idx = i
        if remove_income_idx is not None:
            st.session_state.income_streams.pop(remove_income_idx)
            st.rerun()
        if st.button("+ Add Income Stream", use_container_width=True):
            st.session_state.income_streams.append(
                {"name": "New Income", "monthly": 0.0, "volatility": 0.0}
            )
            st.rerun()

        # ── Fixed Liabilities ──────────────────────────────────────────────
        st.divider()
        st.subheader("Fixed Liabilities")
        liabilities = st.session_state.fixed_liabilities
        remove_liab_idx = None
        for i, liab in enumerate(liabilities):
            with st.expander(liab["name"] or f"Liability {i + 1}", expanded=False):
                liab["name"] = st.text_input(
                    "Name", value=liab["name"], key=f"liab_name_{i}"
                )
                liab["monthly"] = st.number_input(
                    "Monthly ($)",
                    min_value=0.0,
                    value=float(liab["monthly"]),
                    step=50.0,
                    format="%.2f",
                    key=f"liab_monthly_{i}",
                )
                if st.button("Remove", key=f"liab_rm_{i}", type="secondary"):
                    remove_liab_idx = i
        if remove_liab_idx is not None:
            st.session_state.fixed_liabilities.pop(remove_liab_idx)
            st.rerun()
        if st.button("+ Add Fixed Liability", use_container_width=True):
            st.session_state.fixed_liabilities.append(
                {"name": "New Liability", "monthly": 0.0}
            )
            st.rerun()

        # ── Variable Exposures ─────────────────────────────────────────────
        st.divider()
        st.subheader("Variable Exposures")
        exposures = st.session_state.variable_exposures
        remove_exp_idx = None
        for i, exp in enumerate(exposures):
            with st.expander(exp["name"] or f"Exposure {i + 1}", expanded=False):
                exp["name"] = st.text_input(
                    "Name", value=exp["name"], key=f"exp_name_{i}"
                )
                exp["monthly_avg"] = st.number_input(
                    "Monthly Avg ($)",
                    min_value=0.0,
                    value=float(exp["monthly_avg"]),
                    step=50.0,
                    format="%.2f",
                    key=f"exp_monthly_{i}",
                )
                if st.button("Remove", key=f"exp_rm_{i}", type="secondary"):
                    remove_exp_idx = i
        if remove_exp_idx is not None:
            st.session_state.variable_exposures.pop(remove_exp_idx)
            st.rerun()
        if st.button("+ Add Variable Exposure", use_container_width=True):
            st.session_state.variable_exposures.append(
                {"name": "New Exposure", "monthly_avg": 0.0}
            )
            st.rerun()

        # ── Global Settings ────────────────────────────────────────────────
        st.divider()
        st.subheader("Risk Parameters")
        st.session_state.buffer_days = st.number_input(
            "Liquidity Buffer (days)",
            min_value=1,
            max_value=730,
            value=int(st.session_state.buffer_days),
            step=1,
            help="Minimum runway days required before discretionary spend is allowed.",
            key="_buffer_days_input",
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_days(days: float) -> str:
    if not math.isfinite(days):
        return _INF_LABEL
    return f"{days:.1f} days"


def _fmt_currency(amount: float) -> str:
    return format_currency(amount, BASE_CURRENCY)


def _status_color(status: str) -> str:
    return "normal" if status == "SAFE" else ("off" if status == "CRITICAL" else "inverse")


# ---------------------------------------------------------------------------
# Top-row metrics
# ---------------------------------------------------------------------------


def _render_metrics(book: FinanceBook, buffer_days: int) -> None:
    liq: LiquidityResult = liquidity_runway(book)
    lev: LeverageResult = leverage_metrics(book)
    lim: LimitsResult = max_safe_spend_today(book, min_runway_days=buffer_days)
    net_cf = book.monthly_net_cashflow()

    runway_days = liq.runway_days_cash_only
    runway_label = _fmt_days(runway_days)

    lev_ratio = lev.leverage_income_ratio
    lev_label = f"{lev_ratio:.2f}×" if lev_ratio is not None else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Liquidity Runway",
            runway_label,
            help="Cash-only runway: how many days you can sustain current burn without income.",
            delta=liq.status,
            delta_color=_status_color(liq.status),
        )
    with c2:
        st.metric(
            "Personal Leverage",
            lev_label,
            help="Outflows ÷ income. >1× means you are spending more than you earn.",
        )
    with c3:
        st.metric(
            "Max Safe Spend",
            _fmt_currency(lim.max_safe_spend),
            help=f"Maximum discretionary spend today while maintaining {buffer_days}-day liquidity buffer.",
        )
    with c4:
        cf_delta = f"{'+' if net_cf >= 0 else ''}{_fmt_currency(net_cf)}"
        st.metric(
            "Monthly Net Cashflow",
            _fmt_currency(net_cf),
            delta=cf_delta,
            delta_color="normal" if net_cf >= 0 else "inverse",
            help="Total income minus total outflows per month.",
        )

    # Runway gauge chart
    fig_gauge = runway_gauge(runway_days, buffer_days)
    st.plotly_chart(fig_gauge, use_container_width=True)


# ---------------------------------------------------------------------------
# Purchase impact box
# ---------------------------------------------------------------------------


def _render_purchase(book: FinanceBook, buffer_days: int) -> None:
    st.subheader("Purchase Impact Analysis")
    st.caption(
        "Model the risk impact of a one-time purchase on your liquidity and leverage."
    )

    purchase_amount = st.number_input(
        "Purchase Amount ($)",
        min_value=0.0,
        value=0.0,
        step=100.0,
        format="%.2f",
        key="purchase_amount",
    )

    if purchase_amount <= 0:
        st.info("Enter a purchase amount above to see the risk impact.")
        return

    result = evaluate_purchase(book, purchase_amount, min_runway_days=buffer_days)

    # Risk message callout
    pre_runway = result.pre.runway_days_cash_only
    post_runway = result.post.runway_days_cash_only
    breaches_buffer = math.isfinite(post_runway) and post_runway < buffer_days
    if breaches_buffer or result.debt_financed > 0:
        st.warning(result.message)
    else:
        st.success(result.message)

    # Pre / post comparison table
    rows = {
        "Runway (days)": [
            _fmt_days(result.pre.runway_days_cash_only),
            _fmt_days(result.post.runway_days_cash_only),
        ],
        "Leverage (outflows/income)": [
            f"{result.pre.leverage_income_ratio:.3f}×"
            if result.pre.leverage_income_ratio is not None
            else "N/A",
            f"{result.post.leverage_income_ratio:.3f}×"
            if result.post.leverage_income_ratio is not None
            else "N/A",
        ],
        "Max Safe Spend": [
            _fmt_currency(result.pre.max_safe_spend_today),
            _fmt_currency(result.post.max_safe_spend_today),
        ],
    }
    df = pd.DataFrame(rows, index=["Pre-Purchase", "Post-Purchase"]).T
    st.dataframe(df, use_container_width=True)

    if result.debt_financed > 0:
        st.caption(
            f"Debt-financed portion: {_fmt_currency(result.debt_financed)} "
            f"(purchase exceeds available cash)."
        )

    # Pre vs post chart
    fig = purchase_comparison_chart(result.pre, result.post, purchase_amount)
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Stress test section
# ---------------------------------------------------------------------------


def _render_stress(book: FinanceBook, buffer_days: int) -> None:
    st.subheader("Stress Test")
    st.caption(
        "Deterministic scenarios stress your liquidity runway. "
        f"Pass threshold: {buffer_days} days."
    )

    scenario_options = ["Income Drop (%)", "Income Delay (months)", "One-Time Shock ($)"]
    selected = st.selectbox("Scenario", scenario_options, key="stress_scenario")

    col_param, col_result = st.columns([1, 1])

    with col_param:
        if selected == "Income Drop (%)":
            pct = st.slider(
                "Income Drop (%)",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                key="stress_pct_drop",
            )
            active_result = stress_income_drop(
                book, pct_drop=pct / 100, buffer_days=buffer_days
            )
        elif selected == "Income Delay (months)":
            months = st.number_input(
                "Delay (months)",
                min_value=1,
                max_value=24,
                value=3,
                step=1,
                key="stress_delay_months",
            )
            active_result = stress_income_delay(
                book, delay_months=int(months), buffer_days=buffer_days
            )
        else:
            shock = st.number_input(
                "Shock Amount ($)",
                min_value=0.0,
                value=5000.0,
                step=500.0,
                format="%.2f",
                key="stress_shock_amount",
            )
            active_result = stress_one_time_shock(
                book, shock_amount=shock, buffer_days=buffer_days
            )

    with col_result:
        status = active_result.status
        runway = active_result.runway_days
        badge_color = "green" if status == "PASS" else "red"
        st.markdown(
            f"**Result:** :{badge_color}[**{status}**]  \n"
            f"**Runway:** {_fmt_days(runway)}"
        )
        if math.isfinite(runway):
            months_label = (
                f"{active_result.months_to_insolvency:.0f} months to insolvency"
            )
            st.caption(months_label)

    # Full scenario table (default parameters for overview)
    st.markdown("#### All Scenarios Overview")
    drop_r = stress_income_drop(book, pct_drop=0.20, buffer_days=buffer_days)
    delay_r = stress_income_delay(book, delay_months=3, buffer_days=buffer_days)
    shock_r = stress_one_time_shock(
        book,
        shock_amount=book.balance_sheet.cash * 0.25,
        buffer_days=buffer_days,
    )

    overview_data = {
        "Scenario": [
            "Income Drop 20%",
            "Income Delay 3mo",
            "One-Time Shock 25% cash",
        ],
        "Runway (days)": [
            _fmt_days(drop_r.runway_days),
            _fmt_days(delay_r.runway_days),
            _fmt_days(shock_r.runway_days),
        ],
        "Months to Insolvency": [
            _INF_LABEL if not math.isfinite(drop_r.months_to_insolvency)
            else f"{drop_r.months_to_insolvency:.0f}",
            _INF_LABEL if not math.isfinite(delay_r.months_to_insolvency)
            else f"{delay_r.months_to_insolvency:.0f}",
            _INF_LABEL if not math.isfinite(shock_r.months_to_insolvency)
            else f"{shock_r.months_to_insolvency:.0f}",
        ],
        "Status": [drop_r.status, delay_r.status, shock_r.status],
    }
    df_stress = pd.DataFrame(overview_data)
    st.dataframe(df_stress, use_container_width=True, hide_index=True)

    # Stress scenario chart
    fig_stress = stress_comparison_chart(
        [drop_r, delay_r, shock_r], buffer_days=buffer_days
    )
    st.plotly_chart(fig_stress, use_container_width=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _init_state()
    _render_sidebar()

    book = _build_book()
    buffer_days = int(st.session_state.buffer_days)

    st.title(APP_NAME)
    st.caption(APP_DESCRIPTION)
    st.divider()

    # ── Top-row metrics ────────────────────────────────────────────────────
    _render_metrics(book, buffer_days)

    st.divider()

    # ── Purchase impact ────────────────────────────────────────────────────
    _render_purchase(book, buffer_days)

    st.divider()

    # ── Stress tests ───────────────────────────────────────────────────────
    _render_stress(book, buffer_days)


if __name__ == "__main__":
    main()
