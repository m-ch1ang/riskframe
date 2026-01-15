from src.risk.limits import placeholder_limit_breach


def test_placeholder_limit_breach():
    assert placeholder_limit_breach() is False

