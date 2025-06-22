"""Unit tests for utils module.

These tests cover:
- add_allow_header_to_resp header setting
- split_came_case
"""

import pytest
from fastapi import APIRouter, Response

from fed_mgr.utils import add_allow_header_to_resp, split_camel_case


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
