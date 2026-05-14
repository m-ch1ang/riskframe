# Riskframe

A Python application that treats personal finance like a trading book. Built with Streamlit, Riskframe provides risk analytics, liquidity monitoring, leverage tracking, and stress testing for personal financial positions.

## Overview

Riskframe applies institutional risk management principles to personal finance, helping you:
- **Liquidity runway** – Daily burn rate and runway (cash-only and liquid assets), with SAFE/WARN/CRITICAL status (≥180 / 90–179 / &lt;90 days)
- **Leverage metrics** – `leverage_metrics(book)` returns `LeverageResult` with outflows-to-income ratio, an institutional-style outflows-to-net-liquid-worth proxy (denominator clamped to avoid divide-by-zero), fixed-cost coverage (income over fixed outflows), and string flags for edge cases (zero income, non-positive net liquid worth, zero fixed outflows)
- Set and enforce risk limits
- Run stress tests on your financial positions

## Tech Stack

- **Python 3.11+**
- **Streamlit** - Web interface
- **pandas** - Data manipulation
- **numpy** - Numerical computations
- **plotly** - Interactive visualizations
- **pydantic** - Data validation and settings

## Project Structure

```
personal-risk-desk/
├── app.py                 # Streamlit entry point
├── requirements.txt       # Python dependencies
├── src/
│   ├── config/           # Configuration and defaults
│   ├── domain/           # Domain models
│   ├── risk/             # Risk calculation modules
│   ├── charts/           # Visualization utilities
│   └── utils/            # Helper functions
└── tests/                # Test suite
```

## Quickstart

### Prerequisites

- Python 3.11 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd personal-risk-desk
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the app:
```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### Running Tests

```bash
pytest
```

## Development Status

- **Liquidity** – Implemented. `liquidity_runway(book)` returns daily burn, runway days (cash-only and liquid assets), and status from a `FinanceBook`.
- **Leverage** – Implemented. `leverage_metrics(book)` on `src.risk.leverage` returns `LeverageResult` (`leverage_income_ratio`, `leverage_net_liquid`, `fixed_coverage_ratio`, `flags`). Ratios that are undefined return `None` and are described in `flags` (for example `income_zero`, `net_liquid_nonpositive`, `fixed_outflows_zero`). Covered by `tests/test_leverage.py`.
- **Limits** – Implemented. `max_safe_spend_today(book, min_runway_days=42, use_cash_only=True)` returns `LimitsResult` with `min_runway_days`, `required_buffer`, `max_safe_spend`, and `basis` (`CASH_ONLY` or `LIQUID_ASSETS`). Reserves enough balance to cover `min_runway_days` of burn before allowing discretionary spend; when daily burn ≤ 0 the full available balance is spendable. Covered by `tests/test_limits.py`.
- **Purchase Impact** – Implemented. `evaluate_purchase(book, purchase_amount, min_runway_days=42)` in `src.risk.impact` returns `PurchaseImpactResult` with pre/post snapshots (`runway_days_cash_only`, `leverage_income_ratio`, `max_safe_spend_today`), deltas (`delta_runway_days`, `delta_leverage_income_ratio`, `delta_max_safe_spend`), and a human-readable risk-desk message. When `purchase_amount > cash`, the shortfall is modelled as new debt (leverage path): cash is set to zero and `debt` is increased by the overage. Covered by `tests/test_impact.py`.
- **Stress** – Placeholder module; implementation planned.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This is a personal project, but suggestions and feedback are welcome!

---

Happy building!
