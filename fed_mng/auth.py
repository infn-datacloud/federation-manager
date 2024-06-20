"""Authentication and authorization rules."""
import os

import requests
from fastapi import status
from flaat.fastapi import Flaat
from requests.exceptions import ConnectionError, Timeout

from fed_mng.config import get_settings

flaat = Flaat()
flaat.set_trusted_OP_list(get_settings().TRUSTED_IDP_LIST)
flaat.set_request_timeout(30)


def get_user_roles(token: str) -> list[str]:
    """Contact OPA to get user roles.

    Args:
        token (str): access token

    Raises:
        resp.raise_for_status: _description_

    Returns:
        list[str]: User roles
    """
    settings = get_settings()
    data = {"input": {"authorization": f"Bearer {token}"}}
    try:
        resp = requests.post(
            os.path.join(settings.OPA_URL, settings.ROLES_ENDPOINT), json=data
        )
        if resp.status_code == status.HTTP_200_OK:
            return resp.json().get("result", [])
        elif resp.status_code == status.HTTP_400_BAD_REQUEST:
            raise ConnectionRefusedError(
                "Authentication failed: Bad request sent to OPA server."
            )
        elif resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise ConnectionRefusedError(
                "Authentication failed: OPA server internal error."
            )
        else:
            raise ConnectionRefusedError(
                f"Authentication failed: OPA unexpected response code \
                    '{resp.status_code}'."
            )
    except (Timeout, ConnectionError) as e:
        raise ConnectionRefusedError(
            "Authentication failed: OPA server is not reachable."
        ) from e


def has_role(token: str, role: str) -> bool:
    """Validate received token and verify needed rights.

    Contact OPA to verify if the target user has the requested role.
    """
    flaat.get_user_infos_from_access_token(token)
    user_roles = get_user_roles(token)
    return user_roles.get(f"is_{role}", False)
