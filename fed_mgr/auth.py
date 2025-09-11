"""Authentication and authorization rules."""

from logging import Logger
from typing import Annotated

import requests
from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from flaat.exceptions import FlaatUnauthenticated
from flaat.fastapi import Flaat
from flaat.user_infos import UserInfos

from fed_mgr.config import (
    AuthenticationMethodsEnum,
    AuthorizationMethodsEnum,
    Settings,
    SettingsDep,
)

flaat = Flaat()


def configure_flaat(settings: Settings, logger: Logger) -> None:
    """Configure the Flaat authentication and authorization system for the application.

    Sets trusted identity providers, request timeouts, and access levels based on the
    application's authorization mode (email or groups). This function should be called
    at application startup.

    Args:
        settings: The application settings instance.
        logger: The logger instance for logging configuration details.

    """
    logger.info(
        "Trusted IDPs have been configured. Total count: %d",
        len(settings.TRUSTED_IDP_LIST),
    )
    if settings.AUTHN_MODE is None:
        logger.warning("No authentication")
    else:
        logger.info("Authentication mode is %s", settings.AUTHN_MODE.value)
    if settings.AUTHZ_MODE is None:
        logger.warning("No authorization")
    else:
        logger.info("Authorization mode is %s", settings.AUTHZ_MODE.value)
    flaat.set_request_timeout(settings.IDP_TIMEOUT)
    flaat.set_trusted_OP_list([str(i) for i in settings.TRUSTED_IDP_LIST])


security = HTTPBearer()

HttpAuthzCredsDep = Annotated[HTTPAuthorizationCredentials, Security(security)]


def check_flaat_authentication(
    authz_creds: HTTPAuthorizationCredentials, logger: Logger
) -> UserInfos:
    """Verify that the provided access token belongs to a trusted issuer.

    Args:
        authz_creds: HTTP authorization credentials extracted from the request.
        logger (Logger): Logger instance for logging authorization steps.

    Returns:
        UserInfos: The user information extracted from the access token.

    Raises:
        HTTPException: If the token is not valid or not from a trusted issuer.

    """
    logger.debug("Authentication through flaat")
    try:
        return flaat.get_user_infos_from_access_token(authz_creds.credentials)
    except FlaatUnauthenticated as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.render()
        ) from e


def check_authentication(
    request: Request, authz_creds: HttpAuthzCredsDep, settings: SettingsDep
) -> UserInfos:
    """Check user authentication.

    Depending on the authentication mode specified in the settings, this function
    delegates the authentication process to the appropriate handler. If the
    authentication mode is set to 'local', it uses the Flaat authentication mechanism.

    Args:
        request (Request): The current FastAPI request object.
        authz_creds (HttpAuthzCredsDep): The authorization credentials dependency
            required for authentication.
        settings (SettingsDep): The application settings dependency containing
            authentication configuration.

    Returns:
        UserInfos: Information about the authenticated user.

    Raises:
        Exception: If authentication fails or the authentication mode is unsupported.

    """
    if settings.AUTHN_MODE == AuthenticationMethodsEnum.local:
        return check_flaat_authentication(
            authz_creds=authz_creds, logger=request.state.logger
        )
    request.state.logger.debug(
        "No authentication mode. Providing fake user credentials"
    )
    return UserInfos(
        access_token_info=None,
        user_info={"sub": "fake_sub", "iss": "http://fake.iss.it"},
        introspection_info=None,
    )


AuthenticationDep = Annotated[UserInfos, Security(check_authentication)]


async def check_opa_authorization(
    *, request: Request, user_infos: UserInfos, settings: Settings, logger: Logger
) -> None:
    """Check user authorization via Open Policy Agent (OPA).

    Send the request data to the OPA server.

    Args:
        user_infos (UserInfos): The authenticated user information.
        request (Request): The incoming request object containing user information.
        settings (Settings): Application settings containing OPA server configuration.
        logger (Logger): Logger instance for logging authorization steps.

    Returns:
        bool: True if the user is authorized to perform the operation on the endpoint.

    Raises:
        ConnectionRefusedError: If the OPA server returns a bad request, internal error,
            unexpected status code, or is unreachable.

    """
    logger.debug("Authorization through OPA")
    body = await request.body()
    data = {
        "input": {
            "user_info": user_infos.user_info,
            "path": request.url.path,
            "method": request.method,
            "has_body": len(body) > 0,
        }
    }
    try:
        logger.debug("Sending user's data to OPA")
        resp = requests.post(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )
    except (requests.Timeout, ConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Authentication failed: OPA server is not reachable",
        ) from e
    match resp.status_code:
        case status.HTTP_200_OK:
            resp = resp.json().get("result", {"allow": False})
            if resp["allow"]:
                return
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized to perform this operation",
            )
        case status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed: Bad request sent to OPA server",
            )
        case status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed: OPA server internal error",
            )
        case _:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed: OPA unexpected response code "
                f"'{resp.status_code}'",
            )


async def check_authorization(
    request: Request, user_infos: AuthenticationDep, settings: SettingsDep
) -> None:
    """Dependency to check user permissions.

    If the authorization mode is set to 'opa', it uses the OPA authorization mechanism.

    Args:
        request: The current FastAPI request object (provides logger in state).
        user_infos: The authenticated user information.
        settings: The application settings dependency.

    Raises:
        HTTPException: If the user does not have user-level access.

    """
    if settings.AUTHZ_MODE == AuthorizationMethodsEnum.opa:
        return await check_opa_authorization(
            user_infos=user_infos,
            request=request,
            settings=settings,
            logger=request.state.logger,
        )
    return None
