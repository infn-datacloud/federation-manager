"""Unit tests for utils module.

These tests cover:
- add_allow_header_to_resp header setting
- split_came_case
- check_list_not_empty
- retrieve_id_from_entity
"""

import pytest
from fastapi import APIRouter, Response

from fed_mgr.utils import (
    add_allow_header_to_resp,
    check_list_not_empty,
    split_camel_case,
)


class DummyEntity:
    """Dummy entity for testing utility functions."""

    def __init__(self, id):
        """Create a dummy entity with the given ID."""
        self.id = id


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
    ],
)
def test_split_camel_case(input_text, expected):
    """Test that split_camel_case splits camel case strings as expected."""
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
