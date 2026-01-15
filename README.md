# Riskframe

A local-first Python application that treats personal finance like a trading book. Built with Streamlit, Riskframe provides risk analytics, liquidity monitoring, leverage tracking, and stress testing for personal financial positions.

## Overview

Riskframe applies institutional risk management principles to personal finance, helping you:
- Monitor liquidity and cash flow
- Track leverage and exposure
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

🚧 **Early Development** - This is currently a scaffold with placeholder metrics. Risk calculation logic is coming soon.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This is a personal project, but suggestions and feedback are welcome!

---

Happy building! 📊
