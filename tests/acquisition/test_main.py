"""Test for acquisition/main.py."""

from pathlib import Path
from typing import cast

import pytest

from market_sentiment.acquisition import main as main_mod


def test_main_time_from_uses_alpha_vantage_format(
    monkeypatch: pytest.MonkeyPatch, 
    tmp_path: Path, 
    frozen_utc_now: object,
) -> None:
    """Represents orchestration and date window arithmetic.
    
    Alpha Vantage's time_from parameter must be formatted as YYYYMMDDTHHMM (UTC). It
    is calculated as four weeks into the past from the run date, and is captured from
    the params passed to config_alpha_vantage_call.
    """
    monkeypatch.chdir(tmp_path)

    captured: dict[str, object] = {}

    def fake_av_call(tickers: list[str], params: dict[str, str]):
        captured["params"] = params
        return []
    
    monkeypatch.setattr(
        main_mod.alpha_vantage, 
        "config_alpha_vantage_call", 
        fake_av_call
    )

    monkeypatch.setattr(
        main_mod.newsapi,
        "config_news_api_call",
        lambda t, p: []
    )

    monkeypatch.setattr(
        main_mod.r2_uploader,
        "config_r2_upload",
        lambda c: None
    )

    main_mod.main()

    params = cast(dict[str, str], captured["params"])
    assert params["time_from"] == "20260519T1200"
    assert params["fetch_date"] == "2026_06_16"


    