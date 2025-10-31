"""Entry point for the Federation-Registry web app."""

import urllib.parse
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session
from starlette.exceptions import HTTPException

from fed_mgr.auth import configure_flaat
from fed_mgr.config import API_V1_STR, get_settings
from fed_mgr.db import create_db_and_tables, dispose_engine
from fed_mgr.kafka import start_kafka_listeners, stop_kafka_listeners
from fed_mgr.logger import get_logger
from fed_mgr.v1.providers.crud import start_tasks_to_remove_deprecated_providers
from fed_mgr.v1.router import public_router_v1, secured_router_v1
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
    logger = get_logger(settings.LOG_LEVEL)
    configure_flaat(settings, logger)
    engine = create_db_and_tables(logger)

    # At application startup create or delete fake user based on authn mode
    with Session(engine) as session:
        if settings.AUTHN_MODE is None:
            create_fake_user(session)
        else:
            delete_fake_user(session)
        start_tasks_to_remove_deprecated_providers(session)

    if settings.KAFKA_ENABLE:
        kafka_tasks = await start_kafka_listeners(settings, logger)

    yield {"logger": logger}

    if settings.KAFKA_ENABLE:
        await stop_kafka_listeners(kafka_tasks, logger)
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
    allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
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
sub_app_v1.include_router(secured_router_v1)
sub_app_v1.include_router(public_router_v1)


@sub_app_v1.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException errors by returning a JSON response.

    The new object contains the exception's status code and detail.

    Args:
        request (Request): The incoming HTTP request that caused the exception.
        exc (HTTPException): The HTTP exception instance.

    Returns:
        JSONResponse: A JSON response with the status code and detail of the exception.

    """
    return JSONResponse(
        content={"status": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )


app.mount(API_V1_STR, sub_app_v1)
