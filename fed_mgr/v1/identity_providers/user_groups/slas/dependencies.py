"""Dependencies for SLA operations in the slas module."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from fed_mgr.v1.identity_providers.user_groups.slas.crud import get_sla
from fed_mgr.v1.models import SLA

SLADep = Annotated[SLA | None, Depends(get_sla)]


def sla_required(request: Request, idp_id: uuid.UUID, parent_sla: SLADep) -> None:
    """Dependency to ensure the specified user group exists.

    Raises an HTTP 404 error if the user group with the given idp_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        idp_id: The UUID of the user group to check.
        parent_sla: The SLA instance if found, otherwise None.

    Raises:
        HTTPException: If the user group does not exist.

    """
    if parent_sla is None:
        message = f"Identity Provider with ID '{idp_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
