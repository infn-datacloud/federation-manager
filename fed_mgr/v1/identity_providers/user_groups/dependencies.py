"""Dependencies for user group operations in the user groups module."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from fed_mgr.v1.identity_providers.user_groups.crud import get_user_group
from fed_mgr.v1.models import UserGroup

UserGroupDep = Annotated[UserGroup | None, Depends(get_user_group)]


def user_group_required(
    request: Request,
    user_group_id: uuid.UUID,
    user_group: UserGroupDep,
) -> None:
    """Dependency to ensure the specified user group exists.

    Raises an HTTP 404 error if the user group with the given user_group_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        user_group_id: The UUID of the user group to check.
        user_group: The UserGroup instance if found, otherwise None.

    Raises:
        HTTPException: If the user group does not exist.

    """
    if user_group is None:
        message = f"User group with ID '{user_group_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
