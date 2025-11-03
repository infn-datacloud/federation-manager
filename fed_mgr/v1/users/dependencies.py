"""Dependencies for user-related operations in the federation manager."""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from fed_mgr.auth import AuthenticationDep
from fed_mgr.db import SessionDep
from fed_mgr.v1.models import User
from fed_mgr.v1.users.crud import get_user, get_users

UserDep = Annotated[User | None, Depends(get_user)]


def get_current_user(user_infos: AuthenticationDep, session: SessionDep) -> User:
    """Retrieve from the DB the user matching the user submitting the request.

    Args:
        user_infos: The authentication dependency containing user information.
        session: The database session dependency.

    Returns:
        User instance if found, otherwise None.

    """
    users, count = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        sub=user_infos.user_info["sub"],
        issuer=user_infos.user_info["iss"],
    )
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user with the given credentials was found in the DB.",
        )
    return users[0]


CurrenUserDep = Annotated[User, Depends(get_current_user)]
