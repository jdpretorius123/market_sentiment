"""Uploads data into BigQuery.

Functions:
    upload_bq_data(): Uploads clean data into BigQuery.
"""

import hashlib
from typing import Any

from google.cloud import bigquery

from market_sentiment.schemas._variables import SCHEMA
from market_sentiment.schemas.normalized import NormalizedRow


def upload_bq_data(
    bq_project: str, bq_table_ref: str, bq_data: dict[str, NormalizedRow]
) -> None:
    """Uploads clean data into BigQuery.

    Takes clean data and uploads it into BigQuery.

    Args:
        bq_project (str): The BigQuery project.
        bq_table_ref (str): The fully qualified reference of the BigQuery table.
        bq_data (dict[str, NormalizedRow]): Clean data to be stored in BigQuery.
    """
    staging_table_ref = f"{bq_table_ref}_staging"
    target_table_ref = bq_table_ref

    with bigquery.Client(project=bq_project) as client:
        table = bigquery.Table(target_table_ref, schema=SCHEMA)
        table.time_partitioning = bigquery.TimePartitioning(field="published_at")
        table.clustering_fields = ["ticker"]
        table = client.create_table(table, exists_ok=True)

        rows: list[dict[str, Any]] = []
        for key, row in bq_data.items():
            d = row.model_dump()

            # row_id is immutable for idempotency
            d["row_id"] = hashlib.sha256(key.encode()).hexdigest()
            rows.append(d)

        try:
            config = bigquery.LoadJobConfig(
                schema=SCHEMA, write_disposition="WRITE_TRUNCATE"
            )
            load_job = client.load_table_from_json(
                rows, staging_table_ref, job_config=config
            )
            load_job.result()

            merge_query = f"""
                MERGE `{target_table_ref}` AS T
                USING `{staging_table_ref}` AS S
                ON T.row_id = S.row_id
                WHEN NOT MATCHED THEN INSERT ROW
            """
            client.query(merge_query).result()
        finally:
            client.delete_table(staging_table_ref, not_found_ok=True)
