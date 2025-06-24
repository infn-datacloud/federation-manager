"""Dependencies for user group operations in the identity providers module."""

from typing import Annotated

from fastapi import Depends

from fed_mgr.v1.identity_providers.user_groups.crud import get_user_group
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroup

UserGroupDep = Annotated[UserGroup | None, Depends(get_user_group)]
