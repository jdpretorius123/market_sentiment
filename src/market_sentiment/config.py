"""Project-wide variables.

Variables:
    DATA-DESC_BY_SOURCE: API source data descriptions.
    TICKERS: The tickers used for API calls.
    BQ_PROJECT: BigQuery project ID
    DATASET: BigQuery dataset under BQ Project
    TABLE: BigQuery table under BQ Dataset
    BQ_TABLE_REF: Full declared BQ table reference
"""

DATA_DESC_BY_SOURCE = {
    "AlphaVantage": "news_sentiment",
    "NewsAPI": "articles",
}

TICKERS = [
    "MSFT",
    "GOOGL",
    "AMZN",
    "AAPL",
    "DT",
    "RMBS",
    "AKAM",
    "SOUN",
    "CLBT",
    "INSG",
]

BQ_PROJECT = "market-sentiment-intelligence"
DATASET = "market_sentiment"
TABLE = "article_sentiment"
BQ_TABLE_REF = f"{BQ_PROJECT}.{DATASET}.{TABLE}"
