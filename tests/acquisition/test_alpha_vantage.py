"""Tests for acquisition/alpha_vantage.py."""

from typing import Any, cast

import pytest
from requests import RequestException, Session

from market_sentiment.acquisition import alpha_vantage
from market_sentiment.acquisition.alpha_vantage import (
        config_alpha_vantage_call,
        fetch_ticker,
)
from market_sentiment.config import TICKERS
from market_sentiment.schemas.fetch import FetchFailure, FetchResult


# Dummy Classes for Test Execution
class _FakeResponse:
        def __init__(self, payload: Any, status_code: int = 200):
            self._payload = payload
            self.status_code = status_code
            self.text = ""

        def raise_for_status(self):
              return None
        
        def json(self):
              return self._payload


class _FakeSession:
        def __init__(self, response: _FakeResponse):
            self._response = response

        def get(self, url, params=None, timeout=None):
              return self._response
        

class _RaisingSession:
      def get(self, url, params=None, timeout=None):
            raise RequestException("Simulated transport failure.")
      

class _ThrottleResponse:
        def __init__(self, body):
            self.status_code = 200
            self.text = "throttled"
            self._body = body
        
        def raise_for_status(self):
            return None
        
        def json(self):
            return self._body
        

class _ThrottleSession:
        def __init__(self, body):
            self._body = body
        
        def get(self, url, params=None, timeout=None):
            return _ThrottleResponse(self._body)
        

# Tests
def test_fetch_ticker_success_returns_fetchresult(
        av_success_payload: dict[str, object],
        av_api_params: dict[str, str]
) -> None:
    """Represents the HTTP success path and raw payload preservation.
    
    NewsAPI mirrors this pathway. A valid payload produces a FetchResult 
    with the original raw data. Assert source=="AlphaVantage", ticker/endpoint 
    carried through, usuable_data==payload. 
    """
    session = _FakeSession(
          _FakeResponse(av_success_payload, status_code=200)
        )
    result = fetch_ticker(cast(Session, session), av_api_params)

    assert isinstance(result, FetchResult)
    assert result.source == "AlphaVantage"
    assert result.ticker == av_api_params["tickers"]
    assert result.endpoint_url == av_api_params["endpoint_url"]
    assert result.http_status == "200"
    assert result.usable_data == av_success_payload


def test_fetch_ticker_network_error_returns_fetchfailure(
        capsys: pytest.CaptureFixture[str],
        av_api_params: dict[str, str]
) -> None:
    """Represents responsible HTTP-failure response.
    
    NewsAPI mirrors this pathway. A transport failure produces a
    network FetchFailure. Assert error_type=="network", 
    http_status="Unknown", unusuable_data is None, and the error 
    was printed. 
    """
    fail = fetch_ticker(cast(Session, _RaisingSession()), av_api_params)
    captured = capsys.readouterr()

    assert isinstance(fail, FetchFailure)
    assert fail.error_type == "network"
    assert fail.http_status == "Unknown"
    assert fail.unusable_data is None
    assert captured.out.startswith("Network error contacting Alpha Vantage")


@pytest.mark.parametrize("throttle_key" , ["Information", "Note"])
def test_fetch_ticker_rate_limit_returns_fetchfailure(
    throttle_key: str,
    av_api_params: dict[str, str]
    ) -> None:
        """Represents the domain-specific edge case.

        An HTTP-200 body carrying a throttle key ("Information" or "Note") is
        caught as rate_limit. Captures the Alpha Vantage response where throttling 
        returns 200, not 429. Arrange a 200 response whose json() returns
        {throttle_key: <msg>}; assert error_type=="rate_limit" and unusable_data
        holds the decoded payload (not text). 
        """
        body = {throttle_key: "Our standard API rate limit is reached."}
        session = _ThrottleSession(body)

        fail = fetch_ticker(cast(Session, session), av_api_params)

        assert isinstance(fail, FetchFailure)
        assert fail.error_type == "rate_limit"
        assert fail.unusable_data == body
                
        
def test_av_fetch_all_tickers_one_result_per_ticker_in_order(
      monkeypatch: pytest.MonkeyPatch, av_api_params: dict[str, str],
  ) -> None:
      """Represents the guard against silent data loss.
      
      NewsAPI mirrors this pathway. The output should have exactly one entry per input 
      ticker, in input order.
      """
      monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "TEST_KEY")
      monkeypatch.setattr(alpha_vantage.time, "sleep", lambda *_: None)

      def fake_fetch_ticker(session, api_params):
            ticker = api_params["tickers"]
            return FetchResult(
                  fetch_date="2026_06_16",
                  source="AlphaVantage",
                  ticker=ticker,
                  http_status="200",
                  endpoint_url=av_api_params["endpoint_url"],
                  usable_data={}
            )
      
      monkeypatch.setattr(alpha_vantage, "fetch_ticker", fake_fetch_ticker)
      content = config_alpha_vantage_call(TICKERS, av_api_params)

      assert [r.ticker for r in content] == TICKERS
      

def test_config_av_missing_api_key_raises_runtimeerror(
      monkeypatch: pytest.MonkeyPatch, av_api_params: dict[str, str],
  ) -> None:
      """Represents a fail fast mechanism for missing credentials.
      
      NewsAPI mirrors this pathway. A missing ALPHA_VANTAGE_API_KEY raises a
      RuntimeError before any request.
      """
      monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

      with pytest.raises(RuntimeError):
            config_alpha_vantage_call(TICKERS, av_api_params)
      