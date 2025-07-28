"""Endpoints to manage project details."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
    NotNullError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import PROJECTS_PREFIX, PROVIDERS_PREFIX
from fed_mgr.v1.providers.dependencies import ProviderRequiredDep, provider_required
from fed_mgr.v1.providers.projects.crud import (
    add_project,
    delete_project,
    get_projects,
    update_project,
)
from fed_mgr.v1.providers.projects.dependencies import ProjectRequiredDep
from fed_mgr.v1.providers.projects.schemas import (
    ProjectCreate,
    ProjectList,
    ProjectQueryDep,
    ProjectRead,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

project_router = APIRouter(
    prefix=PROVIDERS_PREFIX + "/{provider_id}" + PROJECTS_PREFIX,
    tags=["projects"],
    dependencies=[Depends(provider_required)],
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)


@project_router.options(
    "/",
    summary="List available endpoints for this resource",
    description="List available endpoints for this in the 'Allow' header.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def available_methods(response: Response) -> None:
    """Add the HTTP 'Allow' header to the response.

    Args:
        response (Response): The HTTP response object to which the 'Allow' header will
            be added.

    Returns:
        None

    """
    add_allow_header_to_resp(project_router, response)


@project_router.post(
    "/",
    summary="Create a new project",
    description="Add a new project to the DB. Check if a project's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def create_project(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
    project: ProjectCreate,
) -> ItemID:
    """Create a new project in the system.

    Logs the creation attempt and result. If the project already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the project data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        project (ProjectCreate | None): The project data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        session (SessionDep): The database session dependency.
        provider (Provider): The region's parent provider.

    Returns:
        ItemID: A dictionary containing the ID of the created project on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Creating project with params: {project.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_project = add_project(
            session=session, project=project, created_by=current_user, provider=provider
        )
    except ItemNotFoundError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    except ConflictError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e
    except NotNullError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"Project created: {db_project.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_project.id}


@project_router.get(
    "/",
    summary="Retrieve projects",
    description="Retrieve a paginated list of projects.",
)
def retrieve_projects(
    request: Request,
    session: SessionDep,
    provider: ProviderRequiredDep,
    params: ProjectQueryDep,
) -> ProjectList:
    """Retrieve a paginated list of projects based on query parameters.

    Logs the query parameters and the number of projects retrieved. Fetches
    projects from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the projects in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (ProjectQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.
        provider: Parent provider ID

    Returns:
        ProjectList: A paginated list of projects matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve projects. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    projects, tot_items = get_projects(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        provider_id=provider.id,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved projects: "
    msg += f"{[project.model_dump_json() for project in projects]}"
    request.state.logger.info(msg)
    new_projects = []
    for project in projects:
        new_project = ProjectRead(
            **project.model_dump(),  # Does not return created_by and updated_by
            created_by=project.created_by_id,
            updated_by=project.created_by_id,
            base_url=str(request.url),
        )
        new_projects.append(new_project)
    return ProjectList(
        data=new_projects,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@project_router.get(
    "/{project_id}",
    summary="Retrieve project with given ID",
    description="Check if the given project's ID already exists in the DB "
    "and return it. If the project does not exist in the DB, the endpoint "
    "raises a 404 error.",
)
def retrieve_project(request: Request, project: ProjectRequiredDep) -> ProjectRead:
    """Retrieve a project by their unique identifier.

    Logs the retrieval attempt, checks if the project exists, and returns the
    project object if found. If the project does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        project_id (uuid.UUID): The unique identifier of the project to
            retrieve.
        project (Project | None): The project object, if found.

    Returns:
        Project: The project object if found.
        JSONResponse: A 404 response if the project does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Project with ID '{project.id!s}' found: {project.model_dump_json()}"
    request.state.logger.info(msg)
    project = ProjectRead(
        **project.model_dump(),  # Does not return created_by and updated_by
        created_by=project.created_by_id,
        updated_by=project.created_by_id,
        base_url=str(request.url),
    )
    return project


@project_router.put(
    "/{project_id}",
    summary="Update project with the given id",
    description="Update only a subset of the fields of a project with the "
    "given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_project(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    project_id: uuid.UUID,
    new_project: ProjectCreate,
) -> None:
    """Update an existing project in the database with the given project ID.

    Args:
        request (Request): The current request object.
        project_id (uuid.UUID): The unique identifier of the project to
            update.
        new_project (UserCreate): The new project data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        400 Bad Request: If one of the admin users does not exist in the DB (handled
            below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Update project with ID '{project_id!s}'"
    request.state.logger.info(msg)
    try:
        update_project(
            session=session,
            project_id=project_id,
            new_project=new_project,
            updated_by=current_user,
        )
    except ItemNotFoundError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        ) from e
    except ConflictError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e
    except NotNullError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"Project with ID '{project_id!s}' updated"
    request.state.logger.info(msg)


@project_router.delete(
    "/{project_id}",
    summary="Delete project with given sub",
    description="Delete a project with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage}},
)
def remove_project(
    request: Request, session: SessionDep, project_id: uuid.UUID
) -> None:
    """Remove a project from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_project`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        project_id (uuid.UUID): The unique identifier of the project to be
            removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Delete project with ID '{project_id!s}'"
    request.state.logger.info(msg)
    try:
        delete_project(session=session, project_id=project_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Project with ID '{project_id!s}' deleted"
    request.state.logger.info(msg)
