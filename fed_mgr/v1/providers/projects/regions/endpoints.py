"""Endpoints to manage project-region config details."""

import urllib.parse
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    Security,
    status,
)

from fed_mgr.auth import check_authorization
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    NoItemToUpdateError,
    NotNullError,
    UserNotFoundError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import PROJECTS_PREFIX, PROVIDERS_PREFIX, REGIONS_PREFIX
from fed_mgr.v1.providers.dependencies import provider_required
from fed_mgr.v1.providers.projects.dependencies import ProjectDep, project_required
from fed_mgr.v1.providers.projects.regions.crud import (
    add_project_config,
    delete_project_config,
    get_project_configs,
    update_project_config,
)
from fed_mgr.v1.providers.projects.regions.dependencies import ProjRegConfigDep
from fed_mgr.v1.providers.projects.regions.schemas import (
    ProjRegConfigCreate,
    ProjRegConfigList,
    ProjRegConfigQueryDep,
    ProjRegConfigRead,
)
from fed_mgr.v1.providers.regions.dependencies import RegionDep, region_required
from fed_mgr.v1.schemas import ErrorMessage
from fed_mgr.v1.users.dependencies import CurrenUserDep

proj_reg_link_router = APIRouter(
    prefix=PROVIDERS_PREFIX
    + "/{provider_id}"
    + PROJECTS_PREFIX
    + "/{project_id}"
    + REGIONS_PREFIX,
    tags=["region overrides"],
    dependencies=[
        Security(check_authorization),
        Depends(provider_required),
        Depends(project_required),
    ],
)


@proj_reg_link_router.options(
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
    add_allow_header_to_resp(proj_reg_link_router, response)


@proj_reg_link_router.post(
    "/{region_id}",
    summary="Create a new project",
    description="Add a new project to the DB. Check if a project's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
    dependencies=[Depends(region_required)],
)
def create_project_config(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    overrides: ProjRegConfigCreate,
    project: ProjectDep,
    region: RegionDep,
) -> None:
    """Create a new project in the system.

    Logs the creation attempt and result. If the project already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the project data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        overrides (ProjRegConfigCreate | None): Values overriding the Region default
            ones.
        project (Project): The project instance to connect.
        region (Region): The region instance to connect.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    try:
        request.state.logger.info(
            "Connecting a project with a region with params: %s",
            overrides.model_dump(exclude_none=True),
        )
        db_project = add_project_config(
            session=session,
            overrides=overrides,
            project=project,
            region=region,
            created_by=current_user,
        )
        request.state.logger.info(
            "Project '%s' connected to Region '%s' with params: %s",
            project.id,
            region.id,
            repr(db_project),
        )
        return None
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


@proj_reg_link_router.get(
    "/",
    summary="Retrieve projects",
    description="Retrieve a paginated list of projects.",
)
def retrieve_project_configs(
    request: Request,
    params: ProjRegConfigQueryDep,
    session: SessionDep,
    provider_id: uuid.UUID,
) -> ProjRegConfigList:
    """Retrieve a paginated list of projects based on query parameters.

    Logs the query parameters and the number of projects retrieved. Fetches
    projects from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the projects in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (ProjRegConfigQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.
        provider_id (uuid.UUID): Parent provider ID.

    Returns:
        ProjRegConfigList: A paginated list of projects matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    request.state.logger.info(
        "Retrieve the list of project configurations. Query params: %s",
        params.model_dump(exclude_none=True),
    )
    configs, tot_items = get_project_configs(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    request.state.logger.info(
        "%d retrieved configurations: %s", tot_items, repr(configs)
    )
    new_configs = []
    for config in configs:
        new_config = ProjRegConfigRead(
            **config.model_dump(),  # Does not return created_by and updated_by
            created_by=config.created_by_id,
            updated_by=config.created_by_id,
            links={
                "region": urllib.parse.urljoin(
                    str(request.base_url),
                    f"{PROVIDERS_PREFIX}/{provider_id}/{REGIONS_PREFIX}/{config.region_id}",
                ),
            },
        )
        new_configs.append(new_config)
    return ProjRegConfigList(
        data=new_configs,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@proj_reg_link_router.get(
    "/{region_id}",
    summary="Retrieve project with given ID",
    description="Check if the given project's ID already exists in the DB "
    "and return it. If the project does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
    dependencies=[Depends(region_required)],
)
def retrieve_project_config(
    request: Request,
    project_id: uuid.UUID,
    region_id: uuid.UUID,
    provider_id: uuid.UUID,
    overrides: ProjRegConfigDep,
) -> ProjRegConfigRead:
    """Retrieve a project by their unique identifier.

    Logs the retrieval attempt, checks if the project exists, and returns the
    project object if found. If the project does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        project_id (uuid.UUID): The unique identifier of the project to retrieve.
        region_id (uuid.UUID): The unique identifier of the region to retrieve.
        provider_id (uuid.UUID): The parent provider of both the project and the region.
        overrides (ProjRegConfig | None): The project object, if found.

    Returns:
        ProjRegConfig: The project object if found.
        JSONResponse: A 404 response if the project does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    message = f"Retrieve configuration details of project with ID '{project_id!s}' "
    message += f"linked to region with ID {project_id!a}"
    request.state.logger.info(message)
    if overrides is None:
        message = f"Project with ID '{project_id!s}' does not have a specific "
        message += f"configuration for region with ID '{region_id!s}'"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    message = f"Configuration details for Region with ID '{region_id!s}' "
    message += f"found: {overrides!r}"
    request.state.logger.info(message)
    overrides = ProjRegConfigRead(
        **overrides.model_dump(),  # Does not return created_by and updated_by
        created_by=overrides.created_by_id,
        updated_by=overrides.created_by_id,
        links={
            "region": urllib.parse.urljoin(
                str(request.base_url),
                f"{PROVIDERS_PREFIX}/{provider_id}/{REGIONS_PREFIX}/{overrides.region_id}",
            ),
        },
    )
    return overrides


@proj_reg_link_router.put(
    "/{region_id}",
    summary="Update project with the given id",
    description="Update only a subset of the fields of a project with the "
    "given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
    dependencies=[Depends(region_required)],
)
def edit_project(
    request: Request,
    project_id: uuid.UUID,
    region_id: uuid.UUID,
    new_overrides: ProjRegConfigCreate,
    session: SessionDep,
    current_user: CurrenUserDep,
) -> None:
    """Update an existing project in the database with the given project ID.

    Args:
        request (Request): The current request object.
        project_id (uuid.UUID): The unique identifier of the project to
            update.
        region_id (uuid.UUID): The unique identifier of the region to
            update.
        new_overrides (UserCreate): The new project data to update.
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
    request.state.logger.info("Update project with ID '%s'", str(project_id))
    try:
        update_project_config(
            session=session,
            project_id=project_id,
            region_id=region_id,
            new_overrides=new_overrides,
            updated_by=current_user,
        )
    except NoItemToUpdateError as e:
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
    except UserNotFoundError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    request.state.logger.info(
        "Projec configuration for Region with ID '%s' updated", str(region_id)
    )


@proj_reg_link_router.delete(
    "/{region_id}",
    summary="Delete project with given sub",
    description="Delete a project with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(region_required)],
)
def remove_project(
    request: Request, project_id: uuid.UUID, region_id: uuid.UUID, session: SessionDep
) -> None:
    """Remove a project from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_project`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        project_id (uuid.UUID): The unique identifier of the project to be
            removed
        region_id (uuid.UUID): The unique identifier of the region to be
            removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    request.state.logger.info(
        "Delete configuration for Region with ID '%s'", str(region_id)
    )
    try:
        delete_project_config(
            session=session, project_id=project_id, region_id=region_id
        )
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    request.state.logger.info(
        "Project configuration for Region with ID '%s' deleted", str(region_id)
    )
