"""Dependencies for project configurations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from fed_mgr.v1.models import RegionOverrides
from fed_mgr.v1.providers.projects.regions.crud import get_region_overrides

RegionOverridesDep = Annotated[RegionOverrides | None, Depends(get_region_overrides)]


def region_overrides_required(
    request: Request,
    project_id: uuid.UUID,
    region_id: uuid.UUID,
    region_overrides: RegionOverridesDep,
) -> RegionOverrides:
    """Dependency to ensure the specified identity provider exists.

    Raises an HTTP 404 error if the identity provider with the given idp_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        project_id: The UUID of the identity provider to check.
        region_id: The UUID of the identity provider to check.
        region_overrides: The IdentityProvider instance if found, otherwise None.

    Raises:
        HTTPException: If the identity provider does not exist.

    """
    if region_overrides is None:
        message = f"Project with ID '{project_id!s}' does not define overrides for "
        message += f"region with ID '{region_id!s}'"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return region_overrides


RegionOverridesRequiredDep = Annotated[
    RegionOverrides, Depends(region_overrides_required)
]
