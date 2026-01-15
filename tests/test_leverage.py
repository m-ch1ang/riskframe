from src.risk.leverage import placeholder_leverage_ratio


def test_placeholder_leverage_ratio():
    assert placeholder_leverage_ratio() == 1.0

