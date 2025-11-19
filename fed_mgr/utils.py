"""Utility functions and adapters for specific pydantic types."""

import re

from cryptography.fernet import Fernet
from fastapi import APIRouter, Response
from fastapi.routing import APIRoute


def add_allow_header_to_resp(router: APIRouter, response: Response) -> Response:
    """List in the 'Allow' header the available HTTP methods for the resource.

    Args:
        router (APIRouter): The APIRouter instance containing route definitions.
        response (Response): The FastAPI Response object to modify.

    Returns:
        Response: The response object with the 'Allow' header set.

    """
    allowed_methods: set[str] = set()
    for route in router.routes:
        if isinstance(route, APIRoute):
            allowed_methods.update(route.methods)
    response.headers["Allow"] = ", ".join(allowed_methods)
    return response


def split_camel_case(text: str) -> str:
    """Split a camel case string into words separated by spaces.

    Args:
        text: The camel case string to split.

    Returns:
        str: The string with spaces inserted between camel case words.

    """
    matches = re.finditer(
        r".+?(?:(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z0-9])(?=[A-Z][a-z])|$)", text
    )
    return " ".join([m.group(0) for m in matches])


def encrypt(value: str, fernet: Fernet) -> str:
    """Encrpyt value using fernet method.

    Args:
        fernet (str): Fernet object used to encrypt value
        value (str): value to encrypt

    Returns:
        str: encrypted value.

    """
    return fernet.encrypt(value.encode()).decode()


def decrypt(value: str, fernet: Fernet) -> str:
    """Decrypt value using fernet method.

    Args:
        fernet (str): Fernet object used to decrypt value
        value (str): value to decrypt

    Returns:
        str: decrypted value.

    """
    return fernet.decrypt(value.encode()).decode()
