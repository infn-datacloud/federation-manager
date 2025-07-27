"""Endpoints to manage project-region config details."""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

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
from fed_mgr.v1.providers.dependencies import ProviderRequiredDep, provider_required
from fed_mgr.v1.providers.projects.dependencies import (
    ProjectRequiredDep,
    project_required,
)
from fed_mgr.v1.providers.projects.regions.crud import (
    connect_project_region,
    disconnect_project_region,
    get_region_overrides_list,
    update_region_overrides,
)
from fed_mgr.v1.providers.projects.regions.dependencies import (
    RegionOverridesRequiredDep,
)
from fed_mgr.v1.providers.projects.regions.schemas import (
    ProjRegConnectionCreate,
    ProjRegConnectionList,
    ProjRegConnectionQuery,
    ProjRegConnectionRead,
    RegionOverridesBase,
)
from fed_mgr.v1.providers.regions.crud import get_region
from fed_mgr.v1.providers.regions.dependencies import (
    RegionRequiredDep,
    region_required,
)
from fed_mgr.v1.schemas import ErrorMessage
from fed_mgr.v1.users.dependencies import CurrenUserDep

proj_reg_link_router = APIRouter(
    prefix=PROVIDERS_PREFIX
    + "/{provider_id}"
    + PROJECTS_PREFIX
    + "/{project_id}"
    + REGIONS_PREFIX,
    tags=["region overrides"],
    dependencies=[Depends(provider_required), Depends(project_required)],
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
    project: ProjectRequiredDep,
    config: ProjRegConnectionCreate,
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
        config (ProjRegConfigCreate | None): Values overriding the Region default
            ones.
        project (Project): The project instance to connect.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Connecting project with ID '{project.id!s}' with region with ID "
    msg += f"'{config.region_id!s}' with params: {config.overrides.model_dump_json()}"
    request.state.logger.info(msg)

    region = region_required(
        request=request,
        idp_id=config.region_id,
        idp=get_region(session=session, idp_id=config.region_id),
    )

    try:
        db_overrides = connect_project_region(
            session=session,
            created_by=current_user,
            project=project,
            region=region,
            overrides=config.overrides,
        )
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
    msg = f"Project with ID '{project.id!s}' connected with region with ID "
    msg += f"'{config.region_id!s}' with params: {db_overrides.model_dump_json()}"
    request.state.logger.info(msg)


@proj_reg_link_router.get(
    "/",
    summary="Retrieve projects",
    description="Retrieve a paginated list of projects.",
)
def retrieve_project_configs(
    request: Request,
    session: SessionDep,
    provider: ProviderRequiredDep,
    project: ProjectRequiredDep,
    params: ProjRegConnectionQuery,
) -> ProjRegConnectionList:
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
        project (uuid.UUID): Parent project ID.
        provider (uuid.UUID): Parent project ID.

    Returns:
        ProjRegConfigList: A paginated list of projects matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = "Retrieve region configurations details overwritten by project "
    msg += f"with ID '{project.id!s}'. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    overrides, tot_items = get_region_overrides_list(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        project_id=project.id,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved region configurations details overwritten by project "
    msg += f"with ID '{project.id!s}': "
    msg += f"{[overw.model_dump_json() for overw in overrides]}"
    configs = []
    for overw in overrides:
        config = ProjRegConnectionRead(
            **overw.model_dump(),  # Does not return created_by and updated_by
            overrides=overw,
            created_by=overw.created_by_id,
            updated_by=overw.created_by_id,
            base_url=str(request.base_url),
        )
        configs.append(config)
    return ProjRegConnectionList(
        data=configs,
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
)
def retrieve_project_config(
    request: Request,
    provider: ProviderRequiredDep,
    project: ProjectRequiredDep,
    region: RegionRequiredDep,
    overrides: RegionOverridesRequiredDep,
) -> ProjRegConnectionRead:
    """Retrieve a project by their unique identifier.

    Logs the retrieval attempt, checks if the project exists, and returns the
    project object if found. If the project does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        project (uuid.UUID): The unique identifier of the project to retrieve.
        region (uuid.UUID): The unique identifier of the region to retrieve.
        provider (uuid.UUID): The parent provider of both the project and the region.
        overrides (ProjRegConfig | None): The project object, if found.

    Returns:
        ProjRegConfig: The project object if found.
        JSONResponse: A 404 response if the project does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Configuration details for region with ID '{region.id!s}' "
    msg += f"overwritten by provider with ID '{project.id!s}' found: "
    msg += f"{overrides.model_dump_json()}"
    request.state.logger.info(msg)
    config = ProjRegConnectionRead(
        **overrides.model_dump(),  # Does not return created_by and updated_by
        overrides=overrides,
        created_by=overrides.created_by_id,
        updated_by=overrides.created_by_id,
        base_url=str(request.base_url),
    )
    return config


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
    session: SessionDep,
    current_user: CurrenUserDep,
    project_id: uuid.UUID,
    region_id: uuid.UUID,
    overrides: RegionOverridesBase,
) -> None:
    """Update an existing project in the database with the given project ID.

    Args:
        request (Request): The current request object.
        project_id (uuid.UUID): The unique identifier of the project to
            update.
        region_id (uuid.UUID): The unique identifier of the region to
            update.
        overrides (UserCreate): The new project data to update.
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
    msg = f"Update configuration detail for region with ID '{region_id!s}' "
    msg += f"overwritten by project with ID '{project_id!s}'"
    request.state.logger.info(msg)
    try:
        update_region_overrides(
            session=session,
            project_id=project_id,
            region_id=region_id,
            new_overrides=overrides,
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
    msg = f"Configuration detail for region with ID '{region_id!s}' "
    msg += f"overwritten by project with ID '{project_id!s}' updated"
    request.state.logger.info(msg)


@proj_reg_link_router.delete(
    "/{region_id}",
    summary="Delete project with given sub",
    description="Delete a project with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(region_required)],
)
def remove_project(
    request: Request, session: SessionDep, project_id: uuid.UUID, region_id: uuid.UUID
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
    msg = f"Disconnect region with ID '{region_id!s}' from project with ID "
    msg += f"'{project_id!s}'"
    request.state.logger.info(msg)
    try:
        disconnect_project_region(
            session=session, project_id=project_id, region_id=region_id
        )
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Region with ID '{region_id!s}' disconnected from project with ID "
    msg += f"'{project_id!s}"
    request.state.logger.info(msg)
