"""Entry point for the Federation-Registry web app."""

import urllib.parse
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from fed_mgr.auth import configure_flaat
from fed_mgr.config import API_V1_STR, get_settings
from fed_mgr.db import create_db_and_tables, dispose_engine
from fed_mgr.logger import get_logger
from fed_mgr.v1.router import router as router_v1
from fed_mgr.v1.users.crud import create_fake_user, delete_fake_user

settings = get_settings()

summary = "Federation-Manager REST API of the DataCloud project"
description = """
The Federation-Manager component stores providers federation requests and user groups
resource usage requests.
"""
version = "0.1.0"
contact = {
    "name": settings.MAINTAINER_NAME,
    "url": settings.MAINTAINER_URL,
    "email": settings.MAINTAINER_EMAIL,
}
tags_metadata = [
    {
        "name": API_V1_STR,
        "description": "API version 1, see link on the right",
        "externalDocs": {
            "description": "API version 1 documentation",
            "url": urllib.parse.urljoin(str(settings.BASE_URL), API_V1_STR + "docs"),
        },
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan context manager.

    This function is called at application startup and shutdown. It performs:
    - Initializes the application logger and attaches it to the request state.
    - Configures authentication/authorization (Flaat).
    - Creates database tables if they do not exist.
    - Cleans up resources and disposes the database engine on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        dict: A dictionary with the logger instance, available in the request state.

    """
    logger = get_logger(settings)
    configure_flaat(settings, logger)
    engine = create_db_and_tables(logger)

    # At application startup create or delete fake user based on authn mode
    with Session(engine) as session:
        if settings.AUTHN_MODE is None:
            create_fake_user(session)
        else:
            delete_fake_user(session)

    yield {"logger": logger}

    dispose_engine(logger)


app = FastAPI(
    contact=contact,
    description=description,
    openapi_tags=tags_metadata,
    summary=summary,
    title=settings.PROJECT_NAME,
    version=version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sub_app_v1 = FastAPI(
    contact=contact,
    description=description,
    summary=summary,
    title=settings.PROJECT_NAME,
    version=version,
)
sub_app_v1.include_router(router_v1)
app.mount(API_V1_STR, sub_app_v1)
