"""Tests utilities."""

import string
from random import choices


def random_lower_string() -> str:
    """Return a generic random string."""
    return "".join(choices(string.ascii_lowercase, k=32))
