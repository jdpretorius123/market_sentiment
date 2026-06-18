"""Test for storage/_helpers.py."""

import pytest

from market_sentiment.storage._helpers import verify_env


@pytest.mark.parametrize("value", [None,""])
def test_verify_env_missing_or_empty_raises_runtimeerror(
    value: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Represents the credential validation used by R2 operations.
    
    An unset or empty environment variable raises a RuntimeError.
    """
    if value is None:
        monkeypatch.delenv("R2_ACCESS_KEY_ID", raising=False)
    else:
        monkeypatch.setenv("R2_ACCESS_KEY_ID", value)
    with pytest.raises(RuntimeError):
        verify_env("R2_ACCESS_KEY_ID")
