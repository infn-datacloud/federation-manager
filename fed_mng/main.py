"""Entry point for the Federation-Manager web app."""

import uvicorn
from fastapi import FastAPI, Request, Security
from fastapi.security import HTTPBasicCredentials

# from fastapi.middleware.cors import CORSMiddleware
from fed_mng.auth import flaat, get_user_roles, security
from fed_mng.config import get_settings

# from fed_mng.db import lifespan
from fed_mng.socketio.admin import AdminNamespace
from fed_mng.socketio.site_admin import SiteAdminNamespace
from fed_mng.socketio.site_tester import SiteTesterNamespace
from fed_mng.socketio.sla_mod import SLAModeratorNamespace
from fed_mng.socketio.socket_manager import SocketManager
from fed_mng.socketio.user_group_mgr import UserGroupManagerNamespace

# from fed_mng.router import router_v1


summary = "Federation-Manager of the DataCloud project"
description = """
The Federation-Manager manages the workflows to federate a new provider in the DataCloud
project and the workflows for a user group to request resource to the federated
providers (SLA definition).
"""
version = "0.1.0"

settings = get_settings()

contact = {
    "name": settings.MAINTAINER_NAME,
    "url": settings.MAINTAINER_URL,
    "email": settings.MAINTAINER_EMAIL,
}
# tags_metadata = [
#     {
#         "name": settings.API_V1_STR,
#         "description": "API version 1, see link on the right",
#         "externalDocs": {
#             "description": "API version 1 documentation",
#             "url": f"{settings.DOC_V1_URL}",
#         },
#     },
# ]

app = FastAPI(
    contact=contact,
    description=description,
    # openapi_tags=tags_metadata,
    summary=summary,
    title=settings.PROJECT_NAME,
    version=version,
    # lifespan=lifespan,
)


@app.get("/roles")
@flaat.is_authenticated()
def get_roles(request: Request, credentials: HTTPBasicCredentials = Security(security)):
    """Get user roles. User must be authenticated"""
    return get_user_roles(credentials)


# sub_app_v1 = FastAPI(
#     contact=contact,
#     description=description,
#     summary=summary,
#     title=settings.PROJECT_NAME,
#     version=version,
# )
# sub_app_v1.include_router(router_v1)
# app.mount(settings.API_V1_STR, sub_app_v1)

# Adding the CORS middleware will overwrite SocketManager's CORS settings
# Make sure to add the CORS middleware before SocketManager
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
sio = SocketManager(app=app)

sio.register_namespace(SiteAdminNamespace("/site_admin"))
sio.register_namespace(SiteTesterNamespace("/site_tester"))
sio.register_namespace(UserGroupManagerNamespace("/user_group_mgr"))
sio.register_namespace(SLAModeratorNamespace("/sla_mod"))
sio.register_namespace(AdminNamespace("/admin"))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
