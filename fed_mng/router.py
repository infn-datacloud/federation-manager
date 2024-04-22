"""Module with the router architecture."""
from fastapi import APIRouter

from fed_mng.api.v1.process_specs import router as process_specs_router_v1
from fed_mng.api.v1.users import router as users_router_v1

router_v1 = APIRouter()
router_v1.include_router(process_specs_router_v1)
router_v1.include_router(users_router_v1)
