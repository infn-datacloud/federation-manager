from fastapi import APIRouter, Request, Security
from fastapi.security import HTTPBasicCredentials

from fed_mng.auth import flaat, security
from fed_mng.workflow.manager import engine

router = APIRouter(prefix="/process_specs", tags=["process_specs"])


@router.get(
    "/",
    response_model=list[tuple[str, str, str]],
    summary="Read all process specifications",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("user")
# @db.read_transaction
def get_process_spec_list(
    request: Request,
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
):
    """GET operation to retrieve all flavors.

    It can receive the following group op parameters:
    - comm: parameters common to all DB queries to limit, skip or sort results.
    - page: parameters to limit and select the number of results to return to the user.
    - size: parameters to define the number of information contained in each result.
    - item: parameters specific for this item typology. Used to apply filters.

    Non-authenticated users can view this function. If the user is authenticated the
    user_infos object is not None and it is used to determine the data to return to the
    user.
    """
    return engine.list_specs()

    # if client_credentials:
    #     user_infos = flaat.get_user_infos_from_request(request)
    # else:
    #     user_infos = None
    # items = flavor_mng.get_multi(
    #     **comm.dict(exclude_none=True), **item.dict(exclude_none=True)
    # )
    # items = flavor_mng.paginate(items=items, page=page.page, size=page.size)
    # return flavor_mng.choose_out_schema(
    #     items=items, auth=user_infos, short=size.short, with_conn=size.with_conn
    # )
