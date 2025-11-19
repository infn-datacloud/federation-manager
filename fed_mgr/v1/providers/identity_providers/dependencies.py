"""Dependencies for identity provider operations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Depends

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.models import IdpOverrides
from fed_mgr.v1.providers.identity_providers.crud import get_idp_overrides

IdpOverridesDep = Annotated[IdpOverrides | None, Depends(get_idp_overrides)]


def idp_overrides_required(
    provider_id: uuid.UUID, idp_id: uuid.UUID, idp_overrides: IdpOverridesDep
) -> IdpOverrides:
    """Dependency to ensure the specified identity provider exists.

    Raises an HTTP 404 error if the identity provider with the given idp_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        provider_id: The UUID of the identity provider to check.
        idp_id: The UUID of the identity provider to check.
        idp_overrides: The IdentityProvider instance if found, otherwise None.

    Raises:
        HTTPException: If the identity provider does not exist.

    """
    if idp_overrides is None:
        message = f"Provider with ID '{provider_id!s}' does not define overrides for "
        message += f"identity provider with ID '{idp_id!s}'"
        raise ItemNotFoundError(message)
    return idp_overrides


IdpOverridesRequiredDep = Annotated[IdpOverrides, Depends(idp_overrides_required)]
