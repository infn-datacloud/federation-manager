"""Unit tests for utils module.

These tests cover:
- add_allow_header_to_resp header setting
- split_came_case
- check_list_not_empty
- retrieve_id_from_entity
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import APIRouter, Response

from fed_mgr.utils import (
    add_allow_header_to_resp,
    check_list_not_empty,
    isoformat,
    split_camel_case,
)


def test_add_allow_header_to_resp_sets_methods():
    """Set the Allow header with available HTTP methods."""
    router = APIRouter()

    @router.get("/")
    def dummy():
        """Return a dummy GET response."""
        return "ok"

    @router.post("/")
    def dummy_post():
        """Return a dummy POST response."""
        return "ok"

    response = Response()
    add_allow_header_to_resp(router, response)
    allow = response.headers.get("Allow")
    assert allow is not None
    assert "GET" in allow
    assert "POST" in allow


@pytest.mark.parametrize(
    "input_text,expected",
    [
        ("CamelCase", "Camel Case"),
        ("HTTPRequest", "HTTP Request"),
        ("simpleTest", "simple Test"),
        ("Already Split", "Already Split"),
        ("lowercase", "lowercase"),
        ("", ""),
        ("A", "A"),
        ("CamelCaseStringTest", "Camel Case String Test"),
        ("XMLHttpRequest", "XML Http Request"),
        ("Test123Case", "Test123 Case"),
        ("testABCDef", "test ABC Def"),
        ("JSONData", "JSON Data"),
        ("MyURLParser", "My URL Parser"),
        ("parseIDFromURL", "parse ID From URL"),
        ("aB", "a B"),
        ("AB", "AB"),
        ("AbC", "Ab C"),
        ("Test1Test2", "Test1 Test2"),
        ("test", "test"),
    ],
)
def test_split_camel_case_various_cases(input_text, expected):
    """Test split_camel_case with a variety of camel case and edge case strings."""
    assert split_camel_case(input_text) == expected


def test_check_list_not_empty_returns_list_when_not_empty():
    """Test that check_list_not_empty returns the original list if it is not empty."""
    items = [1, 2, 3]
    result = check_list_not_empty(items)
    assert result == items


def test_check_list_not_empty_raises_on_empty_list():
    """Test that check_list_not_empty raises ValueError if the list is empty."""
    with pytest.raises(ValueError, match="List must not be empty"):
        check_list_not_empty([])


def test_check_list_not_empty_accepts_various_types():
    """Test that check_list_not_empty accept a list with etherogeneus values."""
    assert check_list_not_empty(["a", "b"]) == ["a", "b"]
    assert check_list_not_empty([None]) == [None]


def test_isoformat_utc_datetime():
    """Checks isoformat formats UTC datetime to ISO 8601 with UTC offset."""
    dt = datetime(2024, 6, 1, 12, 34, 56, 789000, tzinfo=timezone.utc)
    result = isoformat(dt)
    assert result == "2024-06-01T12:34:56.789+00:00"


def test_isoformat_naive_datetime():
    """Test that isoformat correctly formats a naive datetime as UTC ISO 8601 string."""
    dt = datetime(2024, 6, 1, 12, 34, 56, 123000)
    # Should treat as local, but isoformat will convert to UTC
    result = isoformat(dt)
    assert result.endswith("2024-06-01T12:34:56.123+00:00")


def test_isoformat_non_utc_datetime():
    """Test that isoformat converts non-UTC datetime to correct UTC ISO format."""
    tz = timezone(timedelta(hours=2))
    dt = datetime(2024, 6, 1, 10, 0, 0, 456000, tzinfo=tz)
    result = isoformat(dt)
    # Should convert to UTC: 08:00:00.456+00:00
    assert result == "2024-06-01T08:00:00.456+00:00"


def test_isoformat_raises_on_invalid_type():
    """Test that isoformat raises AttributeError when input is not a datetime object."""
    with pytest.raises(AttributeError):
        isoformat("not a datetime")
