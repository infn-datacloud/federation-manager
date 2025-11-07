"""Dependencies for resource project operations in the federation manager."""

import uuid
from typing import Annotated

from fastapi import Depends

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.models import Project
from fed_mgr.v1.providers.projects.crud import get_project

ProjectDep = Annotated[Project | None, Depends(get_project)]


def project_required(project_id: uuid.UUID, project: ProjectDep) -> Project:
    """Dependency to ensure the specified resource project exists.

    Raises an HTTP 404 error if the resource project with the given project_id does
    not exist.

    Args:
        request: The current FastAPI request object.
        project_id: The UUID of the resource project to check.
        project: The Project instance if found, otherwise None.

    Raises:
        HTTPException: If the resource project does not exist.

    """
    if project is None:
        raise ItemNotFoundError(f"Project with ID '{project_id!s}' does not exist")
    return project


ProjectRequiredDep = Annotated[Project, Depends(project_required)]
