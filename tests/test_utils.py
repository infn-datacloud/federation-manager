"""Unit tests for utils module.

These tests cover:
- add_allow_header_to_resp header setting
- split_came_case
- check_list_not_empty
- retrieve_id_from_entity
"""

import pytest
from cryptography.fernet import Fernet
from fastapi import APIRouter, Response

from fed_mgr.utils import add_allow_header_to_resp, decrypt, encrypt, split_camel_case


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


def test_encrypt_decrypt_different_keys():
    """Test that encrypt produces different outputs for same value with diff keys."""
    value = "secret"
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()

    enc1 = encrypt(value, key1)
    enc2 = encrypt(value, key2)
    assert enc1 != enc2

    dec1 = decrypt(enc1, key1)
    dec2 = decrypt(enc2, key2)
    assert value == dec1
    assert value == dec2


def test_encrypt_decrypt_different_values():
    """Test that encrypt produces different outputs for diff values with same key."""
    key = Fernet.generate_key()
    value1 = "secret1"
    value2 = "secret2"

    enc1 = encrypt(value1, key)
    enc2 = encrypt(value2, key)
    assert enc1 != enc2

    dec1 = decrypt(enc1, key)
    dec2 = decrypt(enc2, key)
    assert value1 == dec1
    assert value2 == dec2


def test_encrypt_decrypt_empty():
    """Test that encrypt handles empty strings."""
    value = ""
    key = Fernet.generate_key()

    enc = encrypt(value, key)
    assert isinstance(enc, str)
    assert enc != ""

    dec = decrypt(enc, key)
    assert dec == value


def test_encrypt_decrypt_special_chars():
    """Test that encrypt handles special characters."""
    value = "secret!@#$%^&*()"
    key = Fernet.generate_key()

    enc = encrypt(value, key)
    assert isinstance(enc, str)
    assert enc != value

    dec = decrypt(enc, key)
    assert dec == value
