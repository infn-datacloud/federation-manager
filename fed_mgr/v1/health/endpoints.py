"""Endpoints to manage User details."""

import urllib.parse

import requests
from fastapi import APIRouter, Request, status
from requests.exceptions import ConnectionError

from fed_mgr.config import AuthorizationMethodsEnum, SettingsDep
from fed_mgr.db import SessionDep
from fed_mgr.kafka import start_kafka_consumer
from fed_mgr.v1 import HEALTH_PREFIX
from fed_mgr.v1.health.schemas import Health

health_router = APIRouter(prefix=HEALTH_PREFIX, tags=["health"])


@health_router.get(
    "/", summary="Get application health", response_model_exclude_none=True
)
async def liveness_probe(
    request: Request, settings: SettingsDep, session: SessionDep
) -> Health:
    """Restrieve service healthness.

    Check connection with related services.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        settings (SettingsDep): Dependency containing app settings.
        session (SessionDep): Database session dependency.

    Returns:
        Health: single connection status and general service status.

    """
    data = {}
    data["db_connection"] = not session.connection().closed
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.opa:
        try:
            resp = requests.get(
                urllib.parse.urljoin(str(settings.OPA_AUTHZ_URL), "health"),
                timeout=settings.OPA_TIMEOUT,
            )
            data["opa_connection"] = resp.status_code == status.HTTP_200_OK
        except ConnectionError:
            data["opa_connection"] = False
    if settings.KAFKA_ENABLE:
        kafka_consumer = await start_kafka_consumer(
            settings.KAFKA_EVALUATE_PROVIDERS_TOPIC, settings, request.state.logger
        )
        data["kafka_connection"] = kafka_consumer is not None
        if kafka_consumer is not None:
            await kafka_consumer.stop()
    return Health(**data).model_dump()
