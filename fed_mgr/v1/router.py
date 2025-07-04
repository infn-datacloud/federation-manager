"""Module with the V1 router architecture. Include all V1 endpoints."""

from fastapi import APIRouter, status

from fed_mgr.v1.identity_providers.endpoints import idp_router
from fed_mgr.v1.identity_providers.user_groups.endpoints import user_group_router
from fed_mgr.v1.identity_providers.user_groups.slas.endpoints import sla_router
from fed_mgr.v1.locations.endpoints import location_router
from fed_mgr.v1.providers.endpoints import provider_router
from fed_mgr.v1.providers.identity_providers.endpoints import prov_idp_link_router
from fed_mgr.v1.schemas import ErrorMessage
from fed_mgr.v1.users.endpoints import user_router

secured_router_v1 = APIRouter(
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorMessage},
        status.HTTP_403_FORBIDDEN: {"model": ErrorMessage},
    }
)
secured_router_v1.include_router(user_router)
secured_router_v1.include_router(idp_router)
secured_router_v1.include_router(user_group_router)
secured_router_v1.include_router(sla_router)
secured_router_v1.include_router(location_router)
secured_router_v1.include_router(provider_router)
secured_router_v1.include_router(prov_idp_link_router)

public_router_v1 = APIRouter()
