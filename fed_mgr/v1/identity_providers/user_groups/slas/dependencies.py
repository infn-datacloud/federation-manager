"""Dependencies for SLA operations in the slas module."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from fed_mgr.v1.identity_providers.user_groups.slas.crud import get_sla
from fed_mgr.v1.models import SLA

SLADep = Annotated[SLA | None, Depends(get_sla)]


def sla_required(request: Request, sla_id: uuid.UUID, sla: SLADep) -> None:
    """Dependency to ensure the specified SLA exists.

    Raises an HTTP 404 error if the SLA with the given sla_id does not
    exist.

    Args:
        request: The current FastAPI request object.
        sla_id: The UUID of the user group to check.
        sla: The SLA instance if found, otherwise None.

    Raises:
        HTTPException: If the user group does not exist.

    """
    if sla is None:
        message = f"SLA with ID '{sla_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
