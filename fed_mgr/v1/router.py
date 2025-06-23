"""Module with the V1 router architecture. Include all V1 endpoints."""

from fastapi import APIRouter

from fed_mgr.v1.identity_providers.endpoints import idp_router
from fed_mgr.v1.users.endpoints import user_router

router = APIRouter()
router.include_router(user_router)
router.include_router(idp_router)
