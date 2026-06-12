"""Helper functions for transforming data and uploading it into BigQuery.

Functions:
    process_str_list(): Strips, dedupes, and sorts a list.
    canonicalize_authors(): Returns article author(s) information as a cleaned, sorted
        array.
    build_text(): Combines article title and summary into one consolidated text.
    normalize_datetime(): Normalizes formatting for all article publish datetimes.
"""

from datetime import UTC, datetime


def process_str_list(alist: list[str]) -> list[str]:
    """Strips, dedupes, and sorts a list.

    Args:
        alist (list[str]): An uncleaned, unsorted list with duplicates.

    Returns:
        list[str]: A cleaned, deduped, sorted list.
    """
    temp_list = [item.strip() for item in alist]
    temp_list = [item for item in temp_list if item]
    temp_list = list(set(temp_list))
    temp_list.sort()
    return temp_list


def canonicalize_authors(authors: list[str] | str | None) -> list[str]:
    """Returns article author(s) information as a cleaned, sorted array.

    Args:
        authors (list[str] | str | None): Messy, unsorted author(s) information
            from an article.

    Returns:
        list[str]: A cleaned, sorted list of article authors.
    """
    if authors:
        if isinstance(authors, str):
            author_list = authors.split(",")
            author_list = process_str_list(author_list)
        else:
            author_list = process_str_list(authors)

        return author_list
    return []


def build_text(title: str, summary: str | None) -> str:
    """Combines article title and summary into one consolidated text.

    Args:
        title (str): Article title.
        summary (str | None): Article description/summary, depending on source
            (AlphaVantage versus NewsAPI).

    Returns:
        str: Consolidated text containing article title and summary.
    """
    if title:
        consolidated_text = title
    else:
        raise ValueError("title must be supplied.")

    if summary is not None:
        consolidated_text += f"\n\n{summary}"

    return consolidated_text


def normalize_datetime(dt: datetime) -> str:
    """Normalizes formatting for all article publish datetimes.

    Args:
        dt (datetime): Datetime when article was published.

    Returns:
        str: Stringified datetime contract when article was published.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(tz=UTC)

    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
