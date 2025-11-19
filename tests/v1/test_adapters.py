"""Unit tests for adapters.

These tests cover:
- HttpUrlType process_bind_param
- HttpUrlType process_result_value
- HttpUrlType process_literal_param
"""

from pydantic import AnyHttpUrl

from fed_mgr.v1.adapters import HttpUrlType


class DummyDialect:
    """A dummy dialect class for testing purposes."""

    pass


def test_process_bind_param_returns_string():
    """Return string representation of AnyHttpUrl for DB storage."""
    url = AnyHttpUrl("https://example.com/path?q=1")
    result = HttpUrlType().process_bind_param(url, DummyDialect())
    assert result == str(url)


def test_process_result_value_returns_anyhttpurl():
    """Return AnyHttpUrl from string value from DB."""
    url_str = "https://example.com/path?q=1"
    result = HttpUrlType().process_result_value(url_str, DummyDialect())
    assert isinstance(result, AnyHttpUrl)
    assert str(result) == url_str


def test_process_literal_param_returns_string():
    """Return string representation of AnyHttpUrl for SQL literal."""
    url = AnyHttpUrl("https://example.com/path?q=1")
    result = HttpUrlType().process_literal_param(url, DummyDialect())
    assert result == str(url)
