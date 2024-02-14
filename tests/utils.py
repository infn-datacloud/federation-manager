import string
import time
from datetime import date
from random import choice, choices, randint, random

from fed_reg.provider.enum import ProviderStatus, ProviderType
from pydantic import AnyHttpUrl


def random_date() -> date:
    """Return a random date."""
    d = randint(1, int(time.time()))
    return date.fromtimestamp(d)


def random_email() -> str:
    """Return a generic email."""
    return f"{random_lower_string()}@{random_lower_string()}.com"


def random_float(start: int, end: int) -> float:
    """Return a random float between start and end (included)."""
    return randint(start, end - 1) + random()


def random_lower_string() -> str:
    """Return a generic random string."""
    return "".join(choices(string.ascii_lowercase, k=32))


def random_provider_type(*, exclude: list[str] | None = None) -> str:
    """Return one of the possible provider types."""
    if exclude is None:
        exclude = []
    choices = set([i for i in ProviderType]) - set(exclude)
    return choice(list(choices))


def random_provider_status(*, exclude: list[str] | None = None) -> str:
    """Return one of the possible provider statuses."""
    if exclude is None:
        exclude = []
    choices = set([i for i in ProviderStatus]) - set(exclude)
    return choice(list(choices))


def random_start_end_dates() -> tuple[date, date]:
    """Return a random couples of valid start and end dates (in order)."""
    d1 = random_date()
    d2 = random_date()
    while d1 == d2:
        d2 = random_date()
    if d1 < d2:
        start_date = d1
        end_date = d2
    else:
        start_date = d2
        end_date = d1
    return start_date, end_date


def random_url() -> AnyHttpUrl:
    """Return a random URL."""
    return "https://" + random_lower_string() + ".com"
