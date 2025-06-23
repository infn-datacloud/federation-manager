"""Module with the V1 router architecture. Include all V1 endpoints."""

from fastapi import APIRouter, status

from fed_mgr.v1.identity_providers.endpoints import idp_router
from fed_mgr.v1.schemas import ErrorMessage
from fed_mgr.v1.users.endpoints import user_router

router = APIRouter(
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorMessage},
        status.HTTP_403_FORBIDDEN: {"model": ErrorMessage},
    }
)
router.include_router(user_router)
router.include_router(idp_router)
