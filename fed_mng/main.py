"""Entry point for the Federation-Manager web app."""
import uvicorn
from fastapi import FastAPI

from fed_mng.config import get_settings
from fed_mng.router import router_v1

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
tags_metadata = [
    {
        "name": settings.API_V1_STR,
        "description": "API version 1, see link on the right",
        "externalDocs": {
            "description": "API version 1 documentation",
            "url": f"{settings.DOC_V1_URL}",
        },
    },
]

app = FastAPI(
    contact=contact,
    description=description,
    openapi_tags=tags_metadata,
    summary=summary,
    title=settings.PROJECT_NAME,
    version=version,
)

sub_app_v1 = FastAPI(
    contact=contact,
    description=description,
    summary=summary,
    title=settings.PROJECT_NAME,
    version=version,
)
sub_app_v1.include_router(router_v1)
app.mount(settings.API_V1_STR, sub_app_v1)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")