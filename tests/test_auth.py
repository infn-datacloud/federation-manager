"""Unit tests for the authentication and authorization logic in the app.auth module.

Tests performed in this file:

1. test_configure_flaat_sets_trusted_idps:
   Checks that trusted IDPs are set and info is logged.
2. test_configure_flaat_logs_modes:
   Checks logging for authentication/authorization modes.
3. test_check_flaat_authentication_success:
   Ensures user info is returned on successful authentication.
4. test_check_flaat_authentication_failure:
   Ensures HTTP 403 is raised on authentication failure.
5. test_check_authentication_local:
   Checks user info is returned for local authentication.
6. test_check_authentication_none:
   Checks None is returned if authentication mode is None.
7. test_check_opa_authorization_allow:
   Ensures access is allowed when OPA returns allow=True.
8. test_check_opa_authorization_deny:
   Ensures HTTP 401 is raised when OPA returns allow=False.
9. test_check_opa_authorization_bad_request:
   Ensures HTTP 500 is raised on OPA bad request.
10. test_check_opa_authorization_internal_error:
    Ensures HTTP 500 is raised on OPA internal error.
11. test_check_opa_authorization_unexpected_status:
    Ensures HTTP 500 is raised on unexpected OPA status code.
12. test_check_opa_authorization_timeout:
    Ensures HTTP 500 is raised on OPA timeout.
13. test_check_authorization_opa:
    Checks OPA authorization is called when mode is OPA.
14. test_check_authorization_none:
    Ensures no error is raised when authorization mode is None.
"""

from unittest.mock import MagicMock, call, patch

import pytest
import requests
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from flaat.exceptions import FlaatUnauthenticated
from flaat.user_infos import UserInfos

from fed_mgr.auth import (
    check_api_key_authentication,
    check_authentication,
    check_authorization,
    check_flaat_authentication,
    check_opa_authorization,
    configure_flaat,
)
from fed_mgr.config import AuthenticationMethodsEnum, AuthorizationMethodsEnum, Settings
from fed_mgr.exceptions import (
    ServiceUnexpectedResponseError,
    ServiceUnreachableError,
    UnauthenticatedError,
    UnauthorizedError,
)


@pytest.fixture
def authz_creds():
    """Fixture that returns HTTPAuthorizationCredentials with a dummy token."""
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")


@pytest.fixture
def user_infos():
    """Fixture that returns a UserInfos instance with a dummy user."""
    return UserInfos(
        user_info={"sub": "user1"}, access_token_info=None, introspection_info=None
    )


def test_configure_flaat_logs_modes(logger):
    """Test that configure_flaat logs authentication and authorization modes."""
    settings = Settings(AUTHN_MODE=None, AUTHZ_MODE=None)
    configure_flaat(settings, logger)
    logger.warning.assert_has_calls(
        [call("No authentication"), call("No authorization")]
    )

    logger.reset_mock()
    settings = Settings(AUTHN_MODE=AuthenticationMethodsEnum.local, AUTHZ_MODE=None)
    configure_flaat(settings, logger)
    logger.info.assert_any_call("Authentication mode is %s", settings.AUTHN_MODE.value)
    logger.warning.assert_called_once_with("No authorization")

    logger.reset_mock()
    settings = Settings(
        AUTHN_MODE=AuthenticationMethodsEnum.local,
        AUTHZ_MODE=AuthorizationMethodsEnum.opa,
    )
    configure_flaat(settings, logger)
    logger.info.assert_has_calls(
        [
            call("Authentication mode is %s", settings.AUTHN_MODE.value),
            call("Authorization mode is %s", settings.AUTHZ_MODE.value),
        ]
    )


def test_configure_flaat_sets_trusted_idps(logger):
    """Test that configure_flaat sets trusted IDPs and logs the info."""
    settings = Settings(
        AUTHN_MODE=AuthenticationMethodsEnum.local,
        TRUSTED_IDP_LIST=["https://issuer1.com/", "https://issuer2.com/"],
    )
    with patch("fed_mgr.auth.flaat") as mock_flaat:
        configure_flaat(settings, logger)
        mock_flaat.set_trusted_OP_list.assert_called_once_with(
            ["https://issuer1.com/", "https://issuer2.com/"]
        )


def test_check_flaat_authentication_success(authz_creds, logger, user_infos):
    """Test that check_flaat_authentication returns user infos on success."""
    with patch(
        "fed_mgr.auth.flaat.get_user_infos_from_access_token", return_value=user_infos
    ):
        result = check_flaat_authentication(authz_creds, logger)
        assert result == user_infos


def test_check_flaat_authentication_failure(authz_creds, logger):
    """Test that check_flaat_authentication raises HTTPException on authn failure."""
    with patch(
        "fed_mgr.auth.flaat.get_user_infos_from_access_token", return_value=None
    ):
        with pytest.raises(
            UnauthenticatedError, match="User details can't be retrieved"
        ):
            check_flaat_authentication(authz_creds, logger)

    err_msg = "Error message"
    with patch(
        "fed_mgr.auth.flaat.get_user_infos_from_access_token",
        side_effect=FlaatUnauthenticated(err_msg),
    ):
        with pytest.raises(UnauthenticatedError, match=err_msg):
            check_flaat_authentication(authz_creds, logger)


def test_check_api_key_auth_success(logger):
    """Test that check_flaat_authentication returns user infos on success."""
    api_key = "value"
    settings = Settings(API_KEY=api_key)
    result = check_api_key_authentication(api_key, settings, logger)
    assert result is None


def test_check_api_key_auth_error(logger):
    """Test that check_flaat_authentication returns user infos on success."""
    api_key = "value"
    settings = Settings(API_KEY=api_key)
    with pytest.raises(UnauthenticatedError, match="Invalid API Key"):
        check_api_key_authentication("invalid", settings, logger)


def test_check_user_authn_local(authz_creds, user_infos, logger):
    """Test that check_authentication returns user when local authentication is used."""
    settings = Settings(AUTHN_MODE=AuthenticationMethodsEnum.local)
    request = MagicMock()
    request.state.logger = logger
    with patch("fed_mgr.auth.check_flaat_authentication", return_value=user_infos):
        result = check_authentication(request, authz_creds, None, settings)
        assert result == user_infos.user_info


def test_check_script_authn_local(logger):
    """Test that check_authentication returns user when local authentication is used."""
    settings = Settings(AUTHN_MODE=AuthenticationMethodsEnum.local, API_KEY="value")
    request = MagicMock()
    request.state.logger = logger
    result = check_authentication(request, None, settings.API_KEY, settings)
    assert result is None


def test_check_invalid_authn_local(logger):
    """Test that check_authentication returns user when local authentication is used."""
    settings = Settings(AUTHN_MODE=AuthenticationMethodsEnum.local, API_KEY="value")
    request = MagicMock()
    request.state.logger = logger
    with pytest.raises(UnauthenticatedError, match="No credentials provided"):
        check_authentication(request, None, None, settings)


def test_check_authentication_none(logger):
    """Test check_authentication returns fake user creds when authn mode is None."""
    settings = Settings(AUTHN_MODE=None)
    request = MagicMock()
    request.state.logger = logger
    result = check_authentication(request, None, None, settings)
    assert result == {"sub": "fake_sub", "iss": "http://fake.iss.it"}


def test_check_opa_authorization_allow(user_infos, logger):
    """Test that check_opa_authorization allows access when OPA returns allow=True."""
    settings = Settings(
        AUTHN_MODE=AuthenticationMethodsEnum.local,
        AUTHZ_MODE=AuthorizationMethodsEnum.opa,
        OPA_AUTHZ_URL="https://opa.test.com/",
    )
    request = MagicMock()
    request.body.return_value = "data"
    request.url.path = "/test"
    request.method = "GET"
    resp = MagicMock()
    resp.status_code = status.HTTP_200_OK
    resp.json.return_value = {"result": {"allow": True}}
    with patch("requests.post", return_value=resp) as mock_opa:
        result = check_opa_authorization(
            request=request,
            user_info=user_infos.user_info,
            settings=settings,
            logger=logger,
        )
        data = {
            "input": {
                "user_info": user_infos.user_info,
                "path": request.url.path,
                "method": request.method,
                "has_body": True,
            }
        }
        mock_opa.assert_called_once_with(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )
        assert result is None


def test_check_opa_authorization_deny(user_infos, logger):
    """Test that check_opa_authorization denies access when OPA returns allow=False."""
    settings = Settings(
        AUTHN_MODE=AuthenticationMethodsEnum.local,
        AUTHZ_MODE=AuthorizationMethodsEnum.opa,
        OPA_AUTHZ_URL="https://opa.test.com/",
    )
    request = MagicMock()
    request.body.return_value = "data"
    request.url.path = "/test"
    request.method = "GET"
    resp = MagicMock()
    resp.status_code = status.HTTP_200_OK
    resp.json.return_value = {"result": {"allow": False}}
    with patch("requests.post", return_value=resp) as mock_opa:
        with pytest.raises(
            UnauthorizedError, match="Unauthorized to perform this operation"
        ):
            check_opa_authorization(
                request=request,
                user_info=user_infos.user_info,
                settings=settings,
                logger=logger,
            )
        data = {
            "input": {
                "user_info": user_infos.user_info,
                "path": request.url.path,
                "method": request.method,
                "has_body": True,
            }
        }
        mock_opa.assert_called_once_with(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )


@patch("requests.post")
def test_check_opa_authz_err_response(user_infos, logger):
    """Test that check_opa_authorization raises HTTPException on OPA bad request."""
    settings = Settings(
        AUTHN_MODE=AuthenticationMethodsEnum.local,
        AUTHZ_MODE=AuthorizationMethodsEnum.opa,
        OPA_AUTHZ_URL="https://opa.test.com/",
    )
    request = MagicMock()
    request.body.return_value = "data"
    request.url.path = "/test"
    request.method = "GET"
    resp = MagicMock()
    resp.status_code = status.HTTP_400_BAD_REQUEST
    with patch("requests.post", return_value=resp) as mock_opa:
        with pytest.raises(
            ServiceUnexpectedResponseError, match="OPA: Bad request sent to OPA server"
        ):
            check_opa_authorization(
                request=request,
                user_info=user_infos.user_info,
                settings=settings,
                logger=logger,
            )
        data = {
            "input": {
                "user_info": user_infos.user_info,
                "path": request.url.path,
                "method": request.method,
                "has_body": True,
            }
        }
        mock_opa.assert_called_once_with(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )

    resp.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    with patch("requests.post", return_value=resp) as mock_opa:
        with pytest.raises(
            ServiceUnexpectedResponseError, match="OPA: OPA server internal error"
        ):
            check_opa_authorization(
                request=request,
                user_info=user_infos.user_info,
                settings=settings,
                logger=logger,
            )
        data = {
            "input": {
                "user_info": user_infos.user_info,
                "path": request.url.path,
                "method": request.method,
                "has_body": True,
            }
        }
        mock_opa.assert_called_once_with(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )

    resp.status_code = status.HTTP_418_IM_A_TEAPOT
    with patch("requests.post", return_value=resp) as mock_opa:
        with pytest.raises(
            ServiceUnexpectedResponseError, match="OPA: Unexpected response code '418'"
        ):
            check_opa_authorization(
                request=request,
                user_info=user_infos.user_info,
                settings=settings,
                logger=logger,
            )
        data = {
            "input": {
                "user_info": user_infos.user_info,
                "path": request.url.path,
                "method": request.method,
                "has_body": True,
            }
        }
        mock_opa.assert_called_once_with(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )


def test_check_opa_authorization_timeout(user_infos, logger):
    """Test that check_opa_authorization raises HTTPException on OPA timeout."""
    settings = Settings(
        AUTHN_MODE=AuthenticationMethodsEnum.local,
        AUTHZ_MODE=AuthorizationMethodsEnum.opa,
        OPA_AUTHZ_URL="https://opa.test.com/",
    )
    request = MagicMock()
    request.body.return_value = "data"
    request.url.path = "/test"
    request.method = "GET"
    with patch("requests.post", side_effect=requests.Timeout) as mock_opa:
        with pytest.raises(
            ServiceUnreachableError, match="OPA: Server is not reachable"
        ):
            check_opa_authorization(
                request=request,
                user_info=user_infos.user_info,
                settings=settings,
                logger=logger,
            )
        data = {
            "input": {
                "user_info": user_infos.user_info,
                "path": request.url.path,
                "method": request.method,
                "has_body": True,
            }
        }
        mock_opa.assert_called_once_with(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )

    with patch("requests.post", side_effect=ConnectionError) as mock_opa:
        with pytest.raises(
            ServiceUnreachableError, match="OPA: Server is not reachable"
        ):
            check_opa_authorization(
                request=request,
                user_info=user_infos.user_info,
                settings=settings,
                logger=logger,
            )
        data = {
            "input": {
                "user_info": user_infos.user_info,
                "path": request.url.path,
                "method": request.method,
                "has_body": True,
            }
        }
        mock_opa.assert_called_once_with(
            settings.OPA_AUTHZ_URL, json=data, timeout=settings.OPA_TIMEOUT
        )


def test_check_user_authz_opa(user_infos, logger):
    """Test that check_authorization calls OPA authorization when mode is set to OPA."""
    settings = Settings(
        AUTHN_MODE=AuthenticationMethodsEnum.local,
        AUTHZ_MODE=AuthorizationMethodsEnum.opa,
    )
    request = MagicMock()
    request.state.logger = logger
    with patch("fed_mgr.auth.check_opa_authorization", return_value=None):
        result = check_authorization(request, user_infos.user_info, settings)
        assert result is None


def test_check_user_authz_when_disabled(user_infos, logger):
    """Test that check_authorization does not raise when authorization mode is None."""
    settings = Settings(AUTHN_MODE=AuthenticationMethodsEnum.local, AUTHZ_MODE=None)
    request = MagicMock()
    request.state.logger = logger
    result = check_authorization(request, user_infos.user_info, settings)
    assert result is None


def test_check_script_authz_get(logger):
    """Test that check_authorization does not raise when authorization mode is None."""
    settings = Settings(AUTHN_MODE=AuthenticationMethodsEnum.local)
    request = MagicMock()
    request.state.logger = logger
    request.method = "GET"
    result = check_authorization(request, None, settings)
    assert result is None


def test_check_script_authz_forbidden(logger):
    """Test that check_authorization does not raise when authorization mode is None."""
    settings = Settings(AUTHN_MODE=AuthenticationMethodsEnum.local)
    request = MagicMock()
    request.state.logger = logger
    request.method = "POST"
    with pytest.raises(
        UnauthorizedError, match="API Key credentials can be used only for GET requests"
    ):
        check_authorization(request, None, settings)

    request.method = "PUT"
    with pytest.raises(
        UnauthorizedError, match="API Key credentials can be used only for GET requests"
    ):
        check_authorization(request, None, settings)

    request.method = "PATCH"
    with pytest.raises(
        UnauthorizedError, match="API Key credentials can be used only for GET requests"
    ):
        check_authorization(request, None, settings)

    request.method = "DELETE"
    with pytest.raises(
        UnauthorizedError, match="API Key credentials can be used only for GET requests"
    ):
        check_authorization(request, None, settings)
