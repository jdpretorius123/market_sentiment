"""Builds data for charts in the dashboard.

Functions:
    write_json(): Writes BigQuery data to JSON.
    prep_streamgraph(): Prepares data for a streamgraph.
    prep_lollipop(): Prepares data for a lollipop chart.
    prep_network(): Prepares data for a force-directed network graph.
"""

import json
from pathlib import Path
from typing import Any

from market_sentiment.storage.bq_reader import bq_reader

OUTPUT_DIR = Path(__file__).resolve().parents[3] / "docs" / "data"

MIN_EDGE_WEIGHT = 2


def write_json(data: Any, filename: str) -> None:
    """Writes BigQuery data to JSON.

    Args:
        data (Any): Exported BigQuery data.
        filename (str): Name of output file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / filename
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def prep_streamgraph(bq_table_ref: str, bq_project: str) -> list[dict[str, Any]]:
    """Prepares data for a streamgraph.

    The data is grouped by date and an engineered categorical version of sentiment.
    Counts are calculated per group and used to visualize changes in sentiment over
    time.

    Args:
        bq_table_ref (str): Fully qualified table reference to BQ table.
        bq_project (str): Name of the BigQuery project.

    Returns:
        list[dict[str, Any]]: Count data binned by date to reflect changes in sentiment
            (positive, negative, and neutral) over time.

    Raises:
        RuntimeError: Raised if data export from BigQuery fails.
    """
    query = f"""
        WITH spine AS (
            SELECT 
                d AS date 
            FROM 
                UNNEST(GENERATE_DATE_ARRAY(
                    (SELECT MIN(DATE(published_at)) FROM `{bq_table_ref}`),
                    (SELECT MAX(DATE(published_at)) FROM `{bq_table_ref}`))) AS d
        ),
  
        counts AS (
            SELECT 
                DATE(published_at) AS date,
                SUM(CASE WHEN vader_compound >= 0.05 THEN 1 ELSE 0 END) AS pos,
                SUM(CASE WHEN vader_compound <= -0.05 THEN 1 ELSE 0 END) AS neg,
                SUM(
                    CASE WHEN vader_compound > -0.05 AND vader_compound < 0.05 
                        THEN 1 ELSE 0 END
                ) AS neu
            FROM 
                `{bq_table_ref}` 
            GROUP BY 
                date
        )
  
        SELECT 
            spine.date, 
            COALESCE(counts.pos,0) AS pos,
            COALESCE(counts.neu,0) AS neu, 
            COALESCE(counts.neg,0) AS neg
        FROM 
            spine
        LEFT JOIN 
            counts 
        USING 
            (date) 
        ORDER BY 
            spine.date;
    """
    status, rows = bq_reader(bq_project, query)
    if status == "Failure":
        raise RuntimeError(f"Streamgraph data export failed: {rows}")
    for row in rows:
        row["date"] = row["date"].isoformat()
    return rows


def prep_lollipop(
    bq_table_ref: str, bq_project: str, tickers: list[str]
) -> list[dict[str, Any]]:
    """Prepares data for a lollipop chart.

    Each company's net sentiment is calculated by subtracting negative coverage from
    positive coverage. Net sentiment is used to create a lollipop chart downstream.

    Args:
        bq_table_ref (str): Fully qualified table reference to BQ table.
        bq_project (str): Name of the BigQuery project.
        tickers (list[str]): List of pre-determined tickers to track.

    Returns:
        list[dict[str, Any]]: Each company's net sentiment.

    Raises:
        RuntimeError: Raised if data export from BigQuery fails.
    """
    ticker_filter = ", ".join(f"'{ticker}'" for ticker in tickers)
    query = f"""
      SELECT
          ticker,
          AVG(vader_pos) - AVG(vader_neg) AS net
      FROM `{bq_table_ref}`
      WHERE ticker IN ({ticker_filter})
      GROUP BY ticker
      ORDER BY net DESC;
    """
    status, rows = bq_reader(bq_project, query)
    if status == "Failure":
        raise RuntimeError(f"Lollipop data export failed: {rows}")
    return rows


def prep_network(
    bq_table_ref: str, bq_project: str, tickers: list[str]
) -> dict[str, Any]:
    """Prepares data for a force-directed network graph.

    The force-directed network graph displays the strength of association between
    tickers and article topics.

    Args:
        bq_table_ref (str): Fully qualified table reference to BQ table.
        bq_project (str): Name of the BigQuery project.
        tickers (list[str]): List of pre-determined tickers to track.

    Returns:
        dict[str, Any]: Count data binned by ticker and topic to reveal the strength of
            associations between tickers and article topics.

    Raises:
        RuntimeError: Raised if data export from BigQuery fails.
    """
    ticker_filter = ", ".join(f"'{ticker}'" for ticker in tickers)
    nodes_query = f"""
        WITH articles AS (
            SELECT 
                ticker, 
                vader_compound, 
                topics
            FROM 
                `{bq_table_ref}` 
            WHERE 
                provider = 'alpha_vantage'
                AND ticker IN ({ticker_filter})
        ),
        
        ticker_nodes AS (
            SELECT 
                ticker AS id, 
                'ticker' AS type,
                AVG(vader_compound) AS sentiment,
                COUNT(*) AS volume
            FROM 
                articles 
            GROUP BY 
                ticker
        ),
  
        exploded AS (
            SELECT 
                ticker, 
                t.topic, 
                vader_compound 
            FROM 
                articles, 
                UNNEST(topics) AS t
        ),
  
        topic_nodes AS (
            SELECT 
                topic AS id, 
                'topic' AS type,
                AVG(vader_compound) AS sentiment, 
                COUNT(*) AS volume
            FROM 
                exploded 
            GROUP BY 
                topic
        )
  
        SELECT * 
        FROM 
            ticker_nodes 
        UNION ALL 
        SELECT * 
        FROM 
            topic_nodes;
    """

    links_query = f"""
        WITH data AS (
            SELECT
                ticker,
                t.topic
            FROM `{bq_table_ref}`, UNNEST(topics) AS t
            WHERE provider = 'alpha_vantage'
                AND ticker IN ({ticker_filter})    
        )

        SELECT 
            ticker AS source,
            topic AS target,
            COUNT(*) as value
        FROM data
        GROUP BY ticker, topic
        HAVING COUNT(*) >= {MIN_EDGE_WEIGHT};
    """
    node_status, nodes = bq_reader(bq_project, nodes_query)
    if node_status == "Failure":
        raise RuntimeError(f"Network nodes data export failed: {nodes}")

    links_status, links = bq_reader(bq_project, links_query)
    if links_status == "Failure":
        raise RuntimeError(f"Network links data export failed: {links}")

    filtered_ids = {link["source"] for link in links} | {
        link["target"] for link in links
    }
    filtered_nodes = [node for node in nodes if node["id"] in filtered_ids]

    results = {"nodes": filtered_nodes, "links": links}
    return results
