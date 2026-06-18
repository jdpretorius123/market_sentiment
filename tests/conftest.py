"""Fixtures shared by the acquisition phase test suite."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from market_sentiment.schemas.fetch import FetchFailure, FetchResult


# Classes
class FakeS3Client:
    """S3 client for recording put_object calls and exposing close().
    
    put_object(**kwargs) logs the kwargs (Bucket, Key, Body, ContentType,
    Metadata) for assertion. This class can be instantiated to raise a 
    chosen exception so failure-handling paths can be tested. close() records
    call executions, so tests can confirm the client is properly closed.

    Attributes:
        calls ([list[str]]): Call log.
        closed (bool): Flag to indicate that client properly closed.
        _raises (Any | None): An exception to raise, or None.
        _fail_key (str | None): A specific key to test for failure, or None
    """
    def __init__(self, raises=None, fail_key=None):
        """Initializes the FakeS3Client class."""
        self.calls: list[dict[str, object]] = []
        self.closed = False
        self._raises = raises
        self._fail_key = fail_key

    def put_object(self, **kwargs) -> dict[str, object]:
        self.calls.append(kwargs)
        if self._raises is not None and (
            self._fail_key is None or kwargs.get("Key") == self._fail_key
        ):
            raise self._raises
        return {"ResponseMetadata": {"HTTPStatusCode":200}}
    
    def close(self):
        self.closed = True


# Factory fixtures
@pytest.fixture
def make_fetch_result() -> Callable[..., FetchResult]:
    """Return a factory that builds a FetchResult with keyword overrides.

    Defaults must pass setter constraints:
        - "%Y_%m_%d" fetch_date
        - AlphaVantage or NewsAPI source
        - scheme_netloc_path endpoint URL
        - Data from a payload
    Each override (fetch_date, source, ticker, http_status, endpoint_url, usable_data)
    replaces the corresponding default.
    """

    def _make(**kwargs) -> FetchResult:
        data = {
            "fetch_date": "2026_06_16",
            "source": "AlphaVantage",
            "ticker": "AAPL",
            "http_status": "200",
            "endpoint_url": "https://www.alphavantage.co/documentation/#news-sentiment",
            "usable_data": {
                "items":"50",
                "sentiment_score_definition":" ".join([
                    "x <= -0.35: Bearish;",
                    "-0.35 < x <= -0.15: Somewhat-Bearish;",
                    "-0.15 < x < 0.15: Neutral;",
                    "0.15 <= x < 0.35: Somewhat_Bullish;",
                    "x >= 0.35: Bullish",
                ]),
                "relevance_score_definition": " ".join([
                    "0 < x <= 1,",
                    " with a higher score indicating",
                    " higher relevance."
                ]),
                "feed": []
            },
        }
        
        data.update(kwargs)
        return FetchResult(**data)
    return _make


@pytest.fixture
def make_fetch_failure() -> Callable[..., FetchFailure]:
    """Return a factory that builds a FetchFailure with keyword overrides.

    Defaults must pass setter constraints:
        - "%Y_%m_%d" fetch_date
        - AlphaVantage or NewsAPI source
        - Data from a payload
    Each override (fetch_date, source, ticker, http_status, error_type, error_message,
    unusable_data) replaces the corresponding default.
    """

    def _make(**kwargs) -> FetchFailure:
        data = {
            "fetch_date": "2026_06_16",
            "source": "AlphaVantage",
            "ticker": "AAPL",
            "http_status": "unknown",
            "error_message": "Network error contacting Alpha Vantage.",
            "error_type": "network",
            "unusable_data": None,
        }
        data.update(kwargs)
        return FetchFailure(**data)
    return _make


@pytest.fixture
def make_raising_s3_client() -> Callable[..., FakeS3Client]:
    """Return a factory building a FakeS3Client configurable to raise an exception.
    
    Builds a FakeS3Client configurable to raise an exception from put_object.
    """
    def _make(raises: BaseException, fail_key: str | None = None) -> FakeS3Client:
        return FakeS3Client(raises=raises, fail_key=fail_key)
    return _make


@pytest.fixture
def make_av_api_information() -> Callable[..., dict[str, str]]:
    """Return a factory building Alpha Vantage API information."""
    def _make(key: str) -> dict[str, str]:
        return {key:""}
    return _make


# Instance Fixtures
@pytest.fixture
def fake_s3_client() -> FakeS3Client:
    """Return FakeS3Client that records calls and never raises."""
    return FakeS3Client()


# Value Fixtures
@pytest.fixture
def av_api_params() -> dict[str, Any]:
    """Return valid Alpha Vantage API parameters."""
    return {
        "fetch_date": "2026_06_16",
        "endpoint_url": "https://www.alphavantage.co/query",
        "function": "NEWS_SENTIMENT",
        "tickers": "MSFT",
        "topics": "technology",
        "time_from": "20260519T1200",
        "sort": "LATEST",
        "limit": "1000",
        "apikey": "TEST_KEY"
    }


@pytest.fixture
def av_success_payload() -> dict[str, object]:
    """Return a valid Alpha Vantage API payload."""
    return {
            "items":"50",
            "sentiment_score_definition":" ".join([
                "x <= -0.35: Bearish;",
                "-0.35 < x <= -0.15: Somewhat-Bearish;",
                "-0.15 < x < 0.15: Neutral;",
                "0.15 <= x < 0.35: Somewhat_Bullish;",
                "x >= 0.35: Bullish",
            ]),
            "relevance_score_definition":" ".join([
                "0 < x <= 1,",
                " with a higher score indicating",
                " higher relevance."
            ]),
            "feed": []
        }


@pytest.fixture
def frozen_utc_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    """Pin datetime.now(UTC) in acquisition/main.py for window match."""
    frozen = datetime(2026, 6, 16, 12, 0, tzinfo=UTC)
    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None): 
            return frozen
    monkeypatch.setattr("market_sentiment.acquisition.main.datetime", _FrozenDateTime)
    return frozen
