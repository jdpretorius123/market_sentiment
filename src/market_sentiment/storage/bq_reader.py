"""Reads data from BigQuery to JSON for D3 dashboard.

Functions:
    bq_reader(): Reads data from BigQuery.
"""

from typing import Any

from google.api_core.exceptions import (
    GoogleAPICallError,
    RetryError,
)
from google.cloud import bigquery


def bq_reader(bq_project: str, query: str) -> tuple[str, Any]:
    """Reads data from BigQuery.

    Args:
        bq_project (str): The name of the BigQuery project.
        query (str): The query used to pull data from BigQuery.

    Returns:
        tuple[str, Any]: Data from BigQuery.
    """
    try:
        with bigquery.Client(project=bq_project) as client:
            data = client.query(query).result()
            results = [dict(row) for row in data]
        return ("Success", results)

    except (
        GoogleAPICallError,
        RetryError,
    ) as exc:
        err = f"{type(exc).__name__}  {str(exc)}."
        return ("Failure", err)
