"""Dependencies for identity provider operations in the federation manager.

This module defines FastAPI dependencies used for identity provider operations. It
provides dependency functions and types that handle common tasks such as:

- Validating the existence of identity providers
- Loading identity provider data from the database
- Converting database errors to appropriate HTTP responses

Dependencies:
    - IdentityProviderDep: Optional dependency that returns an identity provider
      if found.
    - IdentityProviderRequiredDep: Required dependency that ensures an identity
      provider exists.

Raises:
    - ItemNotFoundError: When a required identity provider is not found
      (translates to HTTP 404 in the API).

See Also:
    - fed_mgr.exceptions.ItemNotFoundError: For error handling details
    - fed_mgr.v1.identity_providers.crud: For the underlying database operations

"""

import uuid
from typing import Annotated

from fastapi import Depends

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.models import IdentityProvider

# Type for a dependency that may return None if the identity provider is not found
IdentityProviderDep = Annotated[IdentityProvider | None, Depends(get_idp)]


def idp_required(idp_id: uuid.UUID, idp: IdentityProviderDep) -> IdentityProvider:
    """Dependency to ensure the specified identity provider exists.

    This dependency checks if the identity provider exists in the database and raises
    an ItemNotFoundError if it doesn't. It's typically used in routes that require a
    valid identity provider to perform their operation. The error is automatically
    converted to a 404 HTTP response by FastAPI's error handlers.

    Args:
        request (Request): The current FastAPI request object, used for logging errors.
        idp_id (uuid.UUID): The UUID of the identity provider to validate.
        idp (IdentityProviderDep): The IdentityProvider instance from the database
            lookup, or None if not found.

    Returns:
        IdentityProvider: The validated identity provider instance.

    Raises:
        ItemNotFoundError: If the identity provider does not exist. This is
            automatically converted to an HTTP 404 response.

    """
    if idp is None:
        raise ItemNotFoundError(
            f"Identity provider with ID '{idp_id!s}' does not exist"
        )
    return idp


# Type for a dependency that guarantees a valid identity provider or raises 404
IdentityProviderRequiredDep = Annotated[IdentityProvider, Depends(idp_required)]
