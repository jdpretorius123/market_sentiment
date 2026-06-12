"""Performs sentiment intensity analysis using the VADER algorithm.

It is assumed that the vader_lexicon is pre-downloaded.

Functions:
    apply_vader(): Applies VADER scoring to a piece of text.
"""

from nltk.sentiment.vader import SentimentIntensityAnalyzer  # type: ignore

analyzer = SentimentIntensityAnalyzer()


def apply_vader(text: str) -> dict[str, float]:
    """Applies VADER scoring to a piece of text.

    Args:
        text (str): Text to be scored.

    Returns:
        dict[str, float]: The four VADER scores (compound, positive, neutral, and
            negative) given to the text.

    Raises:
        ValueError: Raised if the supplied text is None, empty, or whitespace.
    """
    if text.strip():
        scores = analyzer.polarity_scores(text)  # type: ignore
    else:
        raise ValueError("text must not be None, empty, or whitespace.")
    return scores
