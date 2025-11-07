"""Authentication and authorization rules."""

from logging import Logger
from typing import Annotated, Any

import requests
from fastapi import Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from flaat.exceptions import FlaatUnauthenticated
from flaat.fastapi import Flaat
from flaat.user_infos import UserInfos

from fed_mgr.config import (
    AuthenticationMethodsEnum,
    AuthorizationMethodsEnum,
    Settings,
    SettingsDep,
)
from fed_mgr.exceptions import (
    ServiceUnexpectedResponseError,
    ServiceUnreachableError,
    UnauthenticatedError,
    UnauthorizedError,
)

FAKE_USER_NAME = "fake_name"
FAKE_USER_EMAIL = "fake@email.com"
FAKE_USER_SUBJECT = "fake_sub"
FAKE_USER_ISSUER = "https://fake.iss.it"

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
    elif settings.AUTHN_MODE is AuthenticationMethodsEnum.local:
        logger.info("Authentication mode is %s", settings.AUTHN_MODE.value)
        flaat.set_request_timeout(settings.IDP_TIMEOUT)
        flaat.set_trusted_OP_list([str(i) for i in settings.TRUSTED_IDP_LIST])

    if settings.AUTHZ_MODE is None:
        logger.warning("No authorization")
    else:
        logger.info("Authorization mode is %s", settings.AUTHZ_MODE.value)


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
        user_infos = flaat.get_user_infos_from_access_token(authz_creds.credentials)
    except FlaatUnauthenticated as e:
        raise UnauthenticatedError(e.render()["error_description"]) from e
    if user_infos is None:
        raise UnauthenticatedError("User details can't be retrieved")
    return user_infos


def check_api_key_authentication(
    api_key: str, settings: Settings, logger: Logger
) -> None:
    """Verify that the provided access token belongs to a trusted issuer.

    Args:
        api_key (str): API key read from header.
        settings (Settings): settings instance.
        logger (Logger): Logger instance for logging authorization steps.

    Returns:
        UserInfos: The user information extracted from the access token.

    Raises:
        HTTPException: If the token is not valid or not from a trusted issuer.

    """
    logger.debug("Authentication through API Key")
    if settings.API_KEY is None or api_key != settings.API_KEY:
        raise UnauthenticatedError("Invalid API Key")


http_bearer = HTTPBearer(auto_error=False)

HttpAuthzCredsDep = Annotated[
    HTTPAuthorizationCredentials | None, Security(http_bearer)
]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

ApiKeyDep = Annotated[str | None, Security(api_key_header)]


def check_authentication(
    request: Request,
    authz_creds: HttpAuthzCredsDep,
    api_key: ApiKeyDep,
    settings: SettingsDep,
) -> dict[str, Any] | None:
    """Check user authentication.

    Depending on the authentication mode specified in the settings, this function
    delegates the authentication process to the appropriate handler. If the
    authentication mode is set to 'local', it uses the Flaat authentication mechanism.

    Args:
        request (Request): The current FastAPI request object.
        authz_creds (HTTPAuthorizationCredentials): The authorization credentials
            required for authentication when using access token.
        api_key (str): The API key sent into the request's header.
        settings (SettingsDep): The application settings dependency containing
            authentication configuration.

    Returns:
        UserInfos: Information about the authenticated user.

    Raises:
        Exception: If authentication fails or the authentication mode is unsupported.

    """
    if settings.AUTHN_MODE == AuthenticationMethodsEnum.local:
        if authz_creds is not None:
            data = check_flaat_authentication(
                authz_creds=authz_creds, logger=request.state.logger
            )
            return data.user_info
        elif api_key is not None:
            return check_api_key_authentication(
                api_key=api_key, settings=settings, logger=request.state.logger
            )
        else:
            raise UnauthenticatedError("No credentials provided")

    request.state.logger.debug(
        "No authentication mode. Providing fake user credentials"
    )
    return {
        "sub": FAKE_USER_SUBJECT,
        "username": FAKE_USER_NAME,
        "email": FAKE_USER_EMAIL,
        "iss": FAKE_USER_ISSUER,
    }


AuthenticationDep = Annotated[dict[str, Any] | None, Security(check_authentication)]


def check_opa_authorization(
    *, request: Request, user_info: dict[str, Any], settings: Settings, logger: Logger
) -> None:
    """Check user authorization via Open Policy Agent (OPA).

    Send the request data to the OPA server.

    Args:
        user_info (dict): The authenticated user information.
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
    body = request.body()
    data = {
        "input": {
            "user_info": user_info,
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
        raise ServiceUnreachableError("OPA: Server is not reachable") from e
    match resp.status_code:
        case status.HTTP_200_OK:
            resp = resp.json().get("result", {"allow": False})
            if resp["allow"]:
                return None
            raise UnauthorizedError("Unauthorized to perform this operation")
        case status.HTTP_400_BAD_REQUEST:
            raise ServiceUnexpectedResponseError("OPA: Bad request sent to OPA server")
        case status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise ServiceUnexpectedResponseError("OPA: OPA server internal error")
        case _:
            raise ServiceUnexpectedResponseError(
                f"OPA: Unexpected response code '{resp.status_code}'",
            )


def check_authorization(
    request: Request, user_info: AuthenticationDep, settings: SettingsDep
) -> None:
    """Dependency to check user permissions.

    If the authorization mode is set to 'opa', it uses the OPA authorization mechanism.

    Args:
        request: The current FastAPI request object (provides logger in state).
        user_info: The authenticated user information.
        settings: The application settings dependency.

    Raises:
        HTTPException: If the user does not have user-level access.

    """
    if user_info is None:
        # Script based authentication
        if request.method != "GET":
            raise UnauthorizedError(
                "API Key credentials can be used only for GET requests"
            )
    else:
        # User based authentication.
        if settings.AUTHZ_MODE == AuthorizationMethodsEnum.opa:
            return check_opa_authorization(
                user_info=user_info,
                request=request,
                settings=settings,
                logger=request.state.logger,
            )
    return None
