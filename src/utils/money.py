"""Money formatting utilities."""


def format_currency(amount: float | int, currency: str = "USD") -> str:
    """Format numeric amounts with a currency prefix."""
    return f"{currency} {amount:,.2f}"

