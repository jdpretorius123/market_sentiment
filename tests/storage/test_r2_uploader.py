"""Tests for storage/r2_uploader.py."""

import json
from collections.abc import Callable
from typing import cast

from mypy_boto3_s3.client import S3Client

from market_sentiment.schemas.fetch import FetchFailure, FetchResult
from market_sentiment.storage.r2_uploader import upload_all_tickers, upload_ticker
from tests.conftest import FakeS3Client


def test_upload_ticker_passes_expected_key_and_bucket(
        fake_s3_client: FakeS3Client, make_fetch_result: Callable[..., FetchResult]
) -> None:
    """Represents the R2 write contract through a fake S3 client.
    
    Key == "{source}/{ticker}/{fetch_date}/{data_desc}.json" and Bucket == the passed
    bucket_name.
    """
    record = make_fetch_result(
        source="AlphaVantage", 
        ticker="MSFT", 
        fetch_date="2026_06_16"
    )
    bucket = "test_bucket"

    upload_ticker(cast(S3Client, fake_s3_client), record, bucket)

    sent = fake_s3_client.calls[0]
    assert sent["Key"] == "AlphaVantage/MSFT/2026_06_16/news_sentiment.json"
    assert sent["Bucket"] == bucket


def test_upload_ticker_failure_body_has_error_message_and_unusable_data(
        fake_s3_client: FakeS3Client, make_fetch_failure: Callable[..., FetchFailure]
) -> None:
    """Represents the isinstance branch failure versus success pathways.
    
    FetchFailure contain error message, error type, and unusable data if anything is
    returned.
    """
    record = make_fetch_failure(unusable_data={"Note":"throttled"})
    bucket = "test_bucket"

    upload_ticker(cast(S3Client, fake_s3_client), record, bucket)

    body = json.loads(cast(bytes, fake_s3_client.calls[0]["Body"]))
    assert body == {
        "error_message": record.error_message,
        "unusable_data": record.unusable_data
    }


def test_upload_all_tickers_continues_after_one_ticker_fails(
        make_raising_s3_client: Callable[..., FakeS3Client],
        make_fetch_result: Callable[..., FetchResult]
) -> None:
    """Represents partial-failure resilience and configurable fakes.
    
    Only the middle ticker raises, so the other two are attempted. This
    means one failure tuple is returned. Therefore, build the client through
    make_raising_s3_client(raises=..., fail_key=<middle key>) so one upload
    fails. 
    """
    record_one = make_fetch_result(
        source="AlphaVantage",
        ticker="MSFT",
        fetch_date="2026_06_16"
    )
    record_two = make_fetch_result(
        source="NewsAPI",
        ticker="AAPL",
        fetch_date="2026_06_16"
    )
    record_three = make_fetch_result(
        source="NewsAPI",
        ticker="MSFT",
        fetch_date="2026_06_16"
    )
    content = [record_one, record_two, record_three]
    
    bucket = "test_bucket"

    client = make_raising_s3_client(
        raises=TypeError,
        fail_key="NewsAPI/AAPL/2026_06_16/articles.json"
    )
    failures = upload_all_tickers(
        cast(S3Client, client), 
        cast(list[FetchFailure | FetchResult], content), 
        bucket
    )

    assert len(client.calls) == 3
    assert len(failures) == 1

