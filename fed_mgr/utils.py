"""Utility functions and adapters for specific pydantic types."""

import base64
import os
import re

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
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


def encrypt(value: str, secret_key: str) -> str:
    """Encrpyt value using fernet method.

    Args:
        secret_key (str): secret key used to encrypt value
        value (str): value to encrypt

    Returns:
        encrypted string.

    """
    password = secret_key.encode()
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=1_200_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    fernet = Fernet(key)
    return fernet.encrypt(value.encode()).decode()
