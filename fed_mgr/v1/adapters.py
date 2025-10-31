"""Adapters for SQLModel to handle pydantic AnyHttpUrl values.

This module provides a SQLModel/SQLAlchemy TypeDecorator that serializes
pydantic AnyHttpUrl objects to strings for database storage and reconstructs
them when loading from the database.

Classes:
- HttpUrlType: TypeDecorator that converts AnyHttpUrl <-> str.
"""

from pydantic import AnyHttpUrl
from sqlmodel import String, TypeDecorator

MAX_LEN = 255


class HttpUrlType(TypeDecorator):
    """SQL Adapter to translate an HttpUrl into a string and vice versa."""

    impl = String(MAX_LEN)
    cache_ok = True
    python_type = AnyHttpUrl

    def process_bind_param(self, value, dialect) -> str:
        """Convert the AnyHttpUrl value to a string before storing in the database.

        Args:
            value: The AnyHttpUrl value to be stored.
            dialect: The database dialect in use.

        Returns:
            str: The string representation of the URL.

        """
        return str(value)

    def process_result_value(self, value, dialect) -> AnyHttpUrl:
        """Convert the string value from the database back to an AnyHttpUrl.

        Args:
            value: The string value retrieved from the database.
            dialect: The database dialect in use.

        Returns:
            AnyHttpUrl: The reconstructed AnyHttpUrl object.

        """
        return AnyHttpUrl(url=value)

    def process_literal_param(self, value, dialect) -> str:
        """Convert the AnyHttpUrl value to a string for literal SQL statements.

        Args:
            value: The AnyHttpUrl value to be used in a literal SQL statement.
            dialect: The database dialect in use.

        Returns:
            str: The string representation of the URL.

        """
        return str(value)
