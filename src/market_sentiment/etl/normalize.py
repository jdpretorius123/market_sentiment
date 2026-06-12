"""Normalizes cross-source raw API response data for storage in BigQuery.

Functions:
    normalize_alpha_vantage(): Creates a normalized row for storage from raw Alpha
        Vantage responses.
    normalize_newsapi(): Creates a normalized row for storage from raw NewsAPI
        responses.
    unique_rows(): Creates a dictionary of unique rows from two dictionaries.
    build_normalized_rows(): Prepares raw warehousing data for BigQuery upload.
"""

from market_sentiment.etl._helpers import (
    build_text,
    canonicalize_authors,
    normalize_datetime,
)
from market_sentiment.etl.sentiment import apply_vader
from market_sentiment.schemas.alpha_vantage import NewsSentimentResponse
from market_sentiment.schemas.newsapi import EverythingResponse
from market_sentiment.schemas.normalized import NormalizedRow
from market_sentiment.schemas.result import ReadResult


def normalize_alpha_vantage(responses: list[ReadResult]) -> dict[str, NormalizedRow]:
    """Creates a normalized row for storage from raw Alpha Vantage responses.

    Takes raw Alpha Vantage read responses from warehousing and normalizes them
    for storage in BigQuery.

    Args:
        responses (list[ReadResult]): Raw Alpha Vantage read responses.

    Returns:
        dict[str, NormalizedRow]: Normalized storage data.
    """
    normalized_rows: dict[str, NormalizedRow] = {}
    seen_keys: set[str] = set()
    for response in responses:
        metadata = response.upload_metadata
        news_sentiment_response = NewsSentimentResponse.model_validate_json(
            response.usable_data
        )
        for feed_item in news_sentiment_response.feed:
            text = build_text(feed_item.title, feed_item.summary)
            authors = canonicalize_authors(feed_item.authors)
            published_at = normalize_datetime(feed_item.time_published)
            vader_scores = apply_vader(text)

            for ticker in feed_item.ticker_sentiment:
                key_parts = [
                    feed_item.url,
                    feed_item.title,
                    published_at,
                    ticker.ticker,
                ]
                key = "\0".join(key_parts)

                if key not in seen_keys:
                    seen_keys.add(key)
                    arow = NormalizedRow(
                        provider="alpha_vantage",
                        ticker=ticker.ticker,
                        fetch_date=metadata["fetch_date"],
                        published_at=published_at,
                        title=feed_item.title,
                        text=text,
                        url=feed_item.url,
                        source_name=feed_item.source,
                        authors=authors,
                        ticker_sentiment_score=ticker.ticker_sentiment_score,
                        ticker_sentiment_label=ticker.ticker_sentiment_label,
                        topics=feed_item.topics,
                        vader_compound=vader_scores["compound"],
                        vader_pos=vader_scores["pos"],
                        vader_neu=vader_scores["neu"],
                        vader_neg=vader_scores["neg"],
                    )
                    normalized_rows[key] = arow
    return normalized_rows


def normalize_newsapi(responses: list[ReadResult]) -> dict[str, NormalizedRow]:
    """Creates a normalized row for storage from raw NewsAPI responses.

    Takes raw NewsAPI read responses from warehousing and normalizes them
    for storage in BigQuery.

    Args:
        responses (list[ReadResult]): Raw NewsAPI read responses.

    Returns:
        dict[str, NormalizedRow]: Normalized storage data.
    """
    normalized_rows: dict[str, NormalizedRow] = {}
    seen_keys: set[str] = set()
    for response in responses:
        metadata = response.upload_metadata
        newsapi_response = EverythingResponse.model_validate_json(response.usable_data)
        for article in newsapi_response.articles:
            text = build_text(article.title, article.description)
            published_at = normalize_datetime(article.published_at)
            authors = canonicalize_authors(article.author)
            vader_scores = apply_vader(text)

            key_parts = [article.url, article.title, published_at, metadata["ticker"]]
            key = "\0".join(key_parts)

            if key not in seen_keys:
                seen_keys.add(key)
                arow = NormalizedRow(
                    provider="newsapi",
                    ticker=metadata["ticker"],
                    fetch_date=metadata["fetch_date"],
                    published_at=published_at,
                    title=article.title,
                    text=text,
                    url=article.url,
                    source_name=article.source.name,
                    authors=authors,
                    ticker_sentiment_score=None,
                    ticker_sentiment_label=None,
                    topics=[],
                    vader_compound=vader_scores["compound"],
                    vader_pos=vader_scores["pos"],
                    vader_neu=vader_scores["neu"],
                    vader_neg=vader_scores["neg"],
                )
                normalized_rows[key] = arow
    return normalized_rows


def unique_rows(
    alpha_vantage_rows: dict[str, NormalizedRow], newsapi_rows: dict[str, NormalizedRow]
) -> dict[str, NormalizedRow]:
    """Creates a dictionary of unique entries from two dictionaries.

    Args:
        alpha_vantage_rows (dict[str, NormalizedRow]): Normalized Alpha Vantage
            response data (values) with unique row IDs (keys).
        newsapi_rows (dict[str, NormalizedRow]): Normalized NewsAPI response data
            (values) with unique row IDs (keys).

    Returns:
        dict[str, NormalizedRow]: Dictionary of unique entries (row IDs).
    """
    big_query_rows: dict[str, NormalizedRow] = {}
    for key in alpha_vantage_rows.keys():
        if key not in big_query_rows:
            big_query_rows[key] = alpha_vantage_rows[key]
    for key in newsapi_rows.keys():
        if key not in big_query_rows:
            big_query_rows[key] = newsapi_rows[key]
    return big_query_rows


def build_normalized_rows(
    alpha_vantage_responses: list[ReadResult], newsapi_responses: list[ReadResult]
) -> dict[str, NormalizedRow]:
    """Prepares raw warehousing data for BigQuery upload.

    Args:
        alpha_vantage_responses (list[ReadResult]): Raw Alpha Vantage read responses.
        newsapi_responses (list[ReadResult]): Raw NewsAPI read responses.

    Returns:
        dict[str, NormalizedRow]: Dictionary of unique entries.
    """
    alpha_vantage_rows = normalize_alpha_vantage(alpha_vantage_responses)
    newsapi_rows = normalize_newsapi(newsapi_responses)
    bigquery_data = unique_rows(alpha_vantage_rows, newsapi_rows)
    return bigquery_data
