# Riskframe

A local-first personal risk desk that treats your finances like a trading book. Built with Streamlit and Plotly, Riskframe surfaces liquidity runway, leverage exposure, risk limits, and deterministic stress scenarios — using the same vocabulary as an institutional quant desk.

## Overview

Riskframe applies institutional risk management principles to personal finance:

- **Liquidity runway** — Cash-only and liquid-asset runway in days, SAFE/WARN/CRITICAL status (≥180 / 90–179 / <90 days)
- **Personal leverage** — Outflows-to-income ratio; >1× means you are spending more than you earn
- **Risk limits** — Maximum safe discretionary spend enforced by a configurable liquidity buffer
- **Purchase impact analysis** — Pre/post risk snapshot for any prospective purchase, including debt-financed overruns
- **Stress testing** — Three deterministic scenarios (income drop, income delay, one-time shock) with PASS/FAIL verdict and runway comparison chart

## Dashboard

The Streamlit UI (`app.py`) is a single-page dashboard with a sidebar-driven `FinanceBook`:

### Sidebar Inputs

| Section | Fields |
|---|---|
| Balance Sheet | Cash, Investments, Total Debt |
| Income Streams | Name, Monthly amount, Volatility (add/remove) |
| Fixed Liabilities | Name, Monthly amount (add/remove) |
| Variable Exposures | Name, Monthly average (add/remove) |
| Risk Parameters | Liquidity Buffer (days, default 42) |

### Main Dashboard Sections

**Top-Row Metrics**

| Metric | Description |
|---|---|
| Liquidity Runway | Cash-only days at current burn rate |
| Personal Leverage | Total outflows ÷ total income |
| Max Safe Spend Today | Discretionary headroom after reserving the liquidity buffer |
| Monthly Net Cashflow | Income minus all outflows |

A color-coded runway gauge (red/orange/yellow/green) sits below the metrics with a dashed threshold line at the configured buffer.

**Purchase Impact Analysis**

Enter any purchase amount to see:
- Pre vs post runway, leverage ratio, and max safe spend in a comparison table
- A risk-desk message (warning if buffer is breached or debt is taken on)
- Grouped bar chart comparing pre vs post runway days

**Stress Test**

Choose a scenario and tune its parameter:
- **Income Drop (%)** — all income streams scaled down by the chosen percentage
- **Income Delay (months)** — zero income for N months, then normal burn resumes
- **One-Time Shock ($)** — immediate lump-sum expense against current cash

Each scenario shows a PASS/FAIL verdict against the configured buffer, runway days, and months to insolvency. An all-scenarios overview table and horizontal bar chart run all three scenarios simultaneously with default parameters for a quick risk overview.

## Tech Stack

- **Python 3.11+**
- **Streamlit** — dashboard and sidebar state management
- **Plotly** — interactive gauge and bar charts
- **pandas** — tabular results
- **pydantic** — typed schema for `FinanceBook` and all domain models

## Project Structure

```
personal-risk-desk/
├── app.py                 # Streamlit entry point (dashboard)
├── requirements.txt       # Python dependencies
├── src/
│   ├── config/
│   │   ├── defaults.py   # Default FinanceBook and sample data
│   │   └── schema.py     # Pydantic schemas (FinanceBook, IncomeStream, …)
│   ├── domain/           # Domain models (Position, re-exports)
│   ├── risk/
│   │   ├── liquidity.py  # liquidity_runway() → LiquidityResult
│   │   ├── leverage.py   # leverage_metrics() → LeverageResult
│   │   ├── limits.py     # max_safe_spend_today() → LimitsResult
│   │   ├── impact.py     # evaluate_purchase() → PurchaseImpactResult
│   │   └── stress.py     # stress_income_drop/delay/shock → StressTestResult
│   ├── charts/
│   │   └── charts.py     # runway_gauge, purchase_comparison_chart, stress_comparison_chart
│   └── utils/
│       └── money.py      # format_currency()
└── tests/                # Pytest test suite
```

## Quickstart

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

```bash
git clone <your-repo-url>
cd personal-risk-desk
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Dashboard

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

### Run Tests

```bash
pytest
```

## Module Reference

### `src.risk.liquidity`

`liquidity_runway(book) → LiquidityResult`

Returns `daily_burn`, `runway_days_cash_only`, `runway_days_liquid_assets`, and `status` (`SAFE`/`WARN`/`CRITICAL`). Infinite runway when burn ≤ 0.

### `src.risk.leverage`

`leverage_metrics(book) → LeverageResult`

Returns `leverage_income_ratio` (outflows/income, `None` if income is zero), `leverage_net_liquid` (outflows/net-liquid-worth, denominator clamped to 1e-9), `fixed_coverage_ratio` (income/fixed outflows), and `flags` list for edge cases.

### `src.risk.limits`

`max_safe_spend_today(book, min_runway_days=42, use_cash_only=True) → LimitsResult`

Reserves `min_runway_days × daily_burn` as a liquidity buffer; the remainder is spendable. Returns `required_buffer`, `max_safe_spend`, and `basis`.

### `src.risk.impact`

`evaluate_purchase(book, purchase_amount, min_runway_days=42) → PurchaseImpactResult`

Pre/post risk snapshots, deltas, and a human-readable risk message. When the purchase exceeds available cash, the shortfall is modelled as new debt (leverage path).

### `src.risk.stress`

| Function | Scenario |
|---|---|
| `stress_income_drop(book, pct_drop, buffer_days=90)` | All income scaled down by `pct_drop` |
| `stress_income_delay(book, delay_months, buffer_days=90)` | Zero income for N months, normal burn resumes |
| `stress_one_time_shock(book, shock_amount, buffer_days=90)` | Immediate lump-sum cash deduction |

Each returns `StressTestResult` with `runway_days`, `months_to_insolvency`, and `status` (`PASS`/`FAIL` vs `buffer_days`).

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

This is a personal project, but suggestions and feedback are welcome.
