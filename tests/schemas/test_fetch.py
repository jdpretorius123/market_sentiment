"""Test for schemas/fetch.py."""

import pytest

from market_sentiment.schemas.fetch import Fetch


@pytest.mark.parametrize(
    "bad_date", 
    ["N/A", "2026-06-15", "06_15_2026", "2026_13_01", ""]
)
def test_fetch_date_setter_rejects_bad_format(bad_date: str) -> None:
    """fetch_date setter raises ValueError on malformed date strings.

    fetch_date setter raises ValueError on any date string not conforming
    to "YYYY_MM_DD". Parametrized over wrong delimiter, wrong order, 
    impossible month, "N/A", and empty. A Fetch constructed with each raises
    a ValueError from strptime. Represents the data-contract validation layer. 
    """
    with pytest.raises(ValueError):
        Fetch(
            fetch_date=bad_date,
            source="AlphaVantage",
            ticker="MSFT",
            http_status="200"
        )
    