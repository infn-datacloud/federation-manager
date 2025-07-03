"""Dependencies for identity provider operations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.models import IdentityProvider

IdentityProviderDep = Annotated[IdentityProvider | None, Depends(get_idp)]


def idp_required(
    request: Request,
    idp_id: uuid.UUID,
    parent_idp: IdentityProviderDep,
) -> None:
    """Dependency to ensure the specified identity provider exists.

    Raises an HTTP 404 error if the identity provider with the given idp_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        idp_id: The UUID of the identity provider to check.
        parent_idp: The IdentityProvider instance if found, otherwise None.

    Raises:
        HTTPException: If the identity provider does not exist.

    """
    if parent_idp is None:
        message = f"Identity Provider with ID '{idp_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
