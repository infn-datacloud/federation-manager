"""Common Socket.IO utilities."""

from typing import Literal

from flaat.exceptions import FlaatUnauthenticated

from fed_mng.auth import has_role


def validate_auth_on_connect(*, auth: dict[Literal["token"], str], target_role: str):
    """When connecting evaluate user authentication.

    At first check that auth is not None. Then, invoke OPA to check if the
    authenticated user has the target role.
    """
    if auth is None or auth.get("token", None) is None:
        raise ConnectionRefusedError(
            "Authentication failed: No auth data or access token received."
        )
    try:
        assert has_role(auth.get("token", ""), target_role), ConnectionRefusedError(
            "Authentication failed: User does not have needed access rights."
        )
    except FlaatUnauthenticated as e:
        raise ConnectionRefusedError(e) from e
