"""Executes the export and local caching of data from BigQuery."""

import logging
import pathlib
from datetime import UTC, datetime
from typing import Any

from market_sentiment.config import BQ_PROJECT, BQ_TABLE_REF, TICKERS
from market_sentiment.export.build_chart_data import (
    prep_network,
    prep_radar,
    prep_streamgraph,
    write_json,
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Executes the export and local caching of data from BigQuery.

    Initiates the export of data from BigQuery and the subsequent
    local caching of the data to faciliate downstream visualization if
    successful; logs an error log otherwise.
    """
    run_date = datetime.now(UTC).strftime("%Y_%m_%d")
    pathlib.Path("log").mkdir(exist_ok=True)

    log_file = f"log/dashboard_log_{run_date}.txt"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )
    try:
        file_map: dict[str, Any] = {
            "streamgraph_data.json": prep_streamgraph(BQ_TABLE_REF, BQ_PROJECT),
            "radar_data.json": prep_radar(BQ_TABLE_REF, BQ_PROJECT, TICKERS),
            "network_data.json": prep_network(BQ_TABLE_REF, BQ_PROJECT, TICKERS),
        }
    except RuntimeError as exc:
        logger.error("Export aborted: %s", exc)
        return

    for name, payload in file_map.items():
        write_json(payload, name)

    logger.info(
        "Run Summary: streamgraph=%s, radar=%s, nodes=%s, links=%s",
        len(file_map["streamgraph_data.json"]),
        len(file_map["radar_data.json"]),
        len(file_map["network_data.json"]["nodes"]),
        len(file_map["network_data.json"]["links"]),
    )


if __name__ == "__main__":
    main()
