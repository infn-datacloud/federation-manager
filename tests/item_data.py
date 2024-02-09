from datetime import datetime

from tests.utils import random_email, random_lower_string


def user_dict() -> dict[str, str]:
    return {"name": random_lower_string(), "email": random_email()}


def request_dict() -> dict[str, datetime]:
    return {"issue_date": datetime.now(), "update_date": datetime.now()}
