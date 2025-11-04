"""Dependencies for user-related operations in the federation manager."""

import uuid
from typing import Annotated, Literal

from fastapi import Depends

from fed_mgr.auth import AuthenticationDep
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.models import User
from fed_mgr.v1.users.crud import get_user, get_users

UserDep = Annotated[User | None, Depends(get_user)]


def get_current_user(user_info: AuthenticationDep, session: SessionDep) -> User:
    """Retrieve from the DB the user matching the user submitting the request.

    Args:
        user_info: The authentication dependency containing user information.
        session: The database session dependency.

    Returns:
        User instance if found, otherwise None.

    """
    users, count = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        sub=user_info["sub"],
        issuer=user_info["iss"],
    )
    if count == 0:
        raise ItemNotFoundError(
            "No user with the given credentials was found in the DB."
        )
    return users[0]


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def user_required(
    user_id: uuid.UUID | Literal["me"],
    current_user: CurrentUserDep,
    user: UserDep,
) -> User:
    """Dependency to ensure the specified user exists.

    Args:
        request (Request): The current FastAPI request object.
        user_id (uuid.UUID): The UUID of the user to check.
        current_user (User): The user performing the operation.
        user (User | None): The user instance if found, otherwise None.

    Raises:
        ItemNotFoundError: If the user does not exist.

    """
    if user_id == "me":
        return current_user
    if user is None:
        raise ItemNotFoundError(f"User with ID '{user_id!s}' does not exist")
    return user


UserRequiredDep = Annotated[User, Depends(user_required)]
