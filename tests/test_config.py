"""Test for config.py."""

from market_sentiment import config


def test_tickers_has_no_duplicates() -> None:
    """Represents the guard against ticker drifts from config.
    
    len(TICKERS) == len(set(TICKERS)) would flag duplicates,
    which would cause colliding R2 keys and redundant API calls.
    """
    assert len(config.TICKERS) == len(set(config.TICKERS))
    