"""Dependencies for resource provider operations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from fed_mgr.v1.models import Provider
from fed_mgr.v1.providers.crud import get_provider

ProviderDep = Annotated[Provider | None, Depends(get_provider)]


def provider_required(
    request: Request, provider_id: uuid.UUID, provider: ProviderDep
) -> None:
    """Dependency to ensure the specified resource provider exists.

    Raises an HTTP 404 error if the resource provider with the given provider_id does
    not exist.

    Args:
        request: The current FastAPI request object.
        provider_id: The UUID of the resource provider to check.
        provider: The Provider instance if found, otherwise None.

    Raises:
        HTTPException: If the resource provider does not exist.

    """
    if provider is None:
        message = f"Resource provider with ID '{provider_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
