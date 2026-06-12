"""Supplies variables for data transfer between ETL and BigQuery.

Variables:
    SCHEMA: The schema for BigQuery.
"""

from google.cloud import bigquery

SCHEMA = [
    bigquery.SchemaField("row_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("provider", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("ticker", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("fetch_date", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("published_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("text", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("source_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("authors", "STRING", mode="REPEATED"),
    bigquery.SchemaField("ticker_sentiment_score", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("ticker_sentiment_label", "STRING", mode="NULLABLE"),
    bigquery.SchemaField(
        "topics",
        "RECORD",
        mode="REPEATED",
        fields=[
            bigquery.SchemaField("topic", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("relevance_score", "FLOAT64", mode="REQUIRED"),
        ],  # type: ignore
    ),
    bigquery.SchemaField("vader_compound", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("vader_pos", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("vader_neu", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("vader_neg", "FLOAT64", mode="REQUIRED"),
]
