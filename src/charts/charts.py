"""Plotly chart functions for the Riskframe dashboard."""

import math
from typing import Sequence

import plotly.graph_objects as go

from src.risk.impact import PurchaseSnapshot
from src.risk.stress import StressTestResult

_CAP_DAYS = 365  # cap infinite runway for display purposes


def _cap(days: float, cap: float = _CAP_DAYS) -> float:
    """Replace math.inf with a display cap for chart axes."""
    return cap if not math.isfinite(days) else days


def runway_gauge(runway_days: float, buffer_days: int) -> go.Figure:
    """Plotly indicator gauge showing cash-only liquidity runway.

    Color bands:
        red    0 – buffer_days
        orange buffer_days – 90
        yellow 90 – 180
        green  180+
    """
    display_max = max(365, buffer_days * 4)
    value = min(_cap(runway_days), display_max)
    label = "∞" if not math.isfinite(runway_days) else f"{runway_days:.1f} days"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": " days", "font": {"size": 22}},
            title={"text": f"Liquidity Runway<br><sub>({label})</sub>"},
            gauge={
                "axis": {"range": [0, display_max], "tickwidth": 1},
                "bar": {"color": "#4c9be8"},
                "steps": [
                    {"range": [0, buffer_days], "color": "#ff4b4b"},
                    {"range": [buffer_days, 90], "color": "#ffa62b"},
                    {"range": [90, 180], "color": "#ffe08a"},
                    {"range": [180, display_max], "color": "#c3e6cb"},
                ],
                "threshold": {
                    "line": {"color": "#1a1a2e", "width": 3},
                    "thickness": 0.8,
                    "value": buffer_days,
                },
            },
        )
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=60, b=20),
        height=260,
    )
    return fig


def purchase_comparison_chart(
    pre: PurchaseSnapshot,
    post: PurchaseSnapshot,
    purchase_amount: float,
) -> go.Figure:
    """Side-by-side bar chart comparing pre vs post purchase runway."""
    pre_days = _cap(pre.runway_days_cash_only)
    post_days = _cap(post.runway_days_cash_only)

    pre_label = (
        "∞" if not math.isfinite(pre.runway_days_cash_only)
        else f"{pre.runway_days_cash_only:.1f}d"
    )
    post_label = (
        "∞" if not math.isfinite(post.runway_days_cash_only)
        else f"{post.runway_days_cash_only:.1f}d"
    )

    fig = go.Figure(
        data=[
            go.Bar(
                name="Pre-Purchase",
                x=["Runway (days)"],
                y=[pre_days],
                text=[pre_label],
                textposition="outside",
                marker_color="#4c9be8",
            ),
            go.Bar(
                name="Post-Purchase",
                x=["Runway (days)"],
                y=[post_days],
                text=[post_label],
                textposition="outside",
                marker_color="#ff7f7f",
            ),
        ]
    )
    fig.update_layout(
        title=f"Runway Impact: ${purchase_amount:,.0f} Purchase",
        barmode="group",
        yaxis_title="Days",
        legend_title="Position",
        margin=dict(l=20, r=20, t=50, b=20),
        height=320,
    )
    return fig


def stress_comparison_chart(
    results: Sequence[StressTestResult],
    buffer_days: int = 42,
) -> go.Figure:
    """Horizontal bar chart of runway days per stress scenario, colored by PASS/FAIL."""
    scenario_labels = []
    runway_values = []
    colors = []
    text_labels = []

    for r in results:
        scenario_labels.append(r.scenario_name.replace("_", " ").title())
        val = _cap(r.runway_days)
        runway_values.append(val)
        colors.append("#4CAF50" if r.status == "PASS" else "#f44336")
        if not math.isfinite(r.runway_days):
            text_labels.append("∞")
        else:
            text_labels.append(f"{r.runway_days:.1f}d")

    fig = go.Figure(
        go.Bar(
            x=runway_values,
            y=scenario_labels,
            orientation="h",
            text=text_labels,
            textposition="outside",
            marker_color=colors,
        )
    )

    fig.add_vline(
        x=buffer_days,
        line_dash="dash",
        line_color="#e0a800",
        annotation_text=f"Buffer ({buffer_days}d)",
        annotation_position="top right",
    )

    fig.update_layout(
        title="Stress Scenario Runway Comparison",
        xaxis_title="Runway (days)",
        yaxis_title="Scenario",
        margin=dict(l=20, r=40, t=50, b=20),
        height=300,
        showlegend=False,
    )
    return fig
