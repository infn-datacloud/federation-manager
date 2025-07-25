"""Dependencies for resource region operations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from fed_mgr.v1.models import Region
from fed_mgr.v1.providers.regions.crud import get_region

RegionDep = Annotated[Region | None, Depends(get_region)]


def region_required(request: Request, region_id: uuid.UUID, region: RegionDep) -> None:
    """Dependency to ensure the specified resource region exists.

    Raises an HTTP 404 error if the resource region with the given region_id does
    not exist.

    Args:
        request: The current FastAPI request object.
        region_id: The UUID of the resource region to check.
        region: The Region instance if found, otherwise None.

    Raises:
        HTTPException: If the resource region does not exist.

    """
    if region is None:
        message = f"Region with ID '{region_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
