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

from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from flaat.exceptions import FlaatUnauthenticated
from flaat.user_infos import UserInfos

import fed_mgr.auth as auth
from fed_mgr.config import AuthenticationMethodsEnum, AuthorizationMethodsEnum


class DummySettings:
    """A dummy settings class without authentication or authorization."""

    AUTHN_MODE = None
    AUTHZ_MODE = None
    TRUSTED_IDP_LIST: ClassVar[list[str]] = ["https://idp.example.com"]
    OPA_AUTHZ_URL = "http://opa:8181/v1/data/example/allow"


class DummyLogger:
    """A dummy logger class for capturing log messages during tests."""

    def __init__(self):
        """Initialize lists to capture log messages."""
        self.infos = []
        self.warnings = []
        self.debugs = []

    def info(self, msg, *args):
        """Capture info log messages."""
        self.infos.append((msg, args))

    def warning(self, msg):
        """Capture warning log messages."""
        self.warnings.append(msg)

    def debug(self, msg):
        """Capture debug log messages."""
        self.debugs.append(msg)


@pytest.fixture
def logger():
    """Fixture that returns a DummyLogger instance."""
    return DummyLogger()


@pytest.fixture
def settings():
    """Fixture that returns a DummySettings instance."""
    return DummySettings()


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


async def async_body():
    """Return dummy request body data."""
    return b"data"


def test_configure_flaat_sets_trusted_idps(settings, logger):
    """Test that configure_flaat sets trusted IDPs and logs the info."""
    auth.configure_flaat(settings, logger)
    assert len(logger.infos) > 0
    assert any("Trusted IDPs" in msg for msg, _ in logger.infos)


def test_configure_flaat_logs_modes(settings):
    """Test that configure_flaat logs authentication and authorization modes."""
    settings.AUTHN_MODE = None
    settings.AUTHZ_MODE = None
    logger = DummyLogger()
    auth.configure_flaat(settings, logger)
    assert any("No authentication" in msg for msg in logger.warnings)
    assert any("No authorization" in msg for msg in logger.warnings)

    settings.AUTHN_MODE = AuthenticationMethodsEnum.local
    settings.AUTHZ_MODE = AuthorizationMethodsEnum.opa
    logger = DummyLogger()
    auth.configure_flaat(settings, logger)
    assert any("Authentication mode is" in msg for msg, _ in logger.infos)
    assert any("Authorization mode is" in msg for msg, _ in logger.infos)


@patch.object(auth.flaat, "get_user_infos_from_access_token")
def test_check_flaat_authentication_success(
    mock_get_user_infos, authz_creds, logger, user_infos
):
    """Test that check_flaat_authentication returns user infos on success."""
    mock_get_user_infos.return_value = user_infos
    result = auth.check_flaat_authentication(authz_creds, logger)
    assert result == user_infos
    assert "Authentication through flaat" in logger.debugs


@patch.object(auth.flaat, "get_user_infos_from_access_token")
def test_check_flaat_authentication_failure(mock_get_user_infos, authz_creds, logger):
    """Test that check_flaat_authentication raises HTTPException on authn failure."""
    mock_get_user_infos.side_effect = FlaatUnauthenticated("fail")
    with pytest.raises(HTTPException) as exc:
        auth.check_flaat_authentication(authz_creds, logger)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


@patch("fed_mgr.auth.check_flaat_authentication")
def test_check_authentication_local(
    mock_check, authz_creds, settings, user_infos, logger
):
    """Test that check_authentication returns user when local authentication is used."""
    settings.AUTHN_MODE = auth.AuthenticationMethodsEnum.local
    request = MagicMock()
    request.state.logger = logger
    mock_check.return_value = user_infos
    result = auth.check_authentication(request, authz_creds, settings)
    assert result == user_infos


def test_check_authentication_none(authz_creds, settings, logger):
    """Test that check_authentication returns None when authentication mode is None."""
    settings.AUTHN_MODE = None
    request = MagicMock()
    request.state.logger = logger
    result = auth.check_authentication(request, authz_creds, settings)
    assert result is None


@pytest.mark.asyncio
@patch("requests.post")
async def test_check_opa_authorization_allow(mock_post, user_infos, settings, logger):
    """Test that check_opa_authorization allows access when OPA returns allow=True."""

    class DummyResp:
        status_code = status.HTTP_200_OK

        def json(self):
            return {"result": {"allow": True}}

    request = MagicMock()
    request.body = async_body
    request.url.path = "/test"
    request.method = "GET"

    mock_post.return_value = DummyResp()

    await auth.check_opa_authorization(
        request=request, user_infos=user_infos, settings=settings, logger=logger
    )
    assert "Authorization through OPA" in logger.debugs
    assert "Sending user's data to OPA" in logger.debugs


@pytest.mark.asyncio
@patch("requests.post")
async def test_check_opa_authorization_deny(mock_post, user_infos, settings, logger):
    """Test that check_opa_authorization denies access when OPA returns allow=False."""

    class DummyResp:
        status_code = status.HTTP_200_OK

        def json(self):
            return {"result": {"allow": False}}

    request = MagicMock()
    request.body = async_body
    request.url.path = "/test"
    request.method = "GET"

    mock_post.return_value = DummyResp()

    with pytest.raises(HTTPException) as exc:
        await auth.check_opa_authorization(
            request=request, user_infos=user_infos, settings=settings, logger=logger
        )
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@patch("requests.post")
async def test_check_opa_authorization_bad_request(
    mock_post, user_infos, settings, logger
):
    """Test that check_opa_authorization raises HTTPException on OPA bad request."""

    class DummyResp:
        status_code = status.HTTP_400_BAD_REQUEST

    request = MagicMock()
    request.body = async_body
    request.url.path = "/test"
    request.method = "GET"

    mock_post.return_value = DummyResp()

    with pytest.raises(HTTPException) as exc:
        await auth.check_opa_authorization(
            request=request, user_infos=user_infos, settings=settings, logger=logger
        )
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@patch("requests.post")
async def test_check_opa_authorization_internal_error(
    mock_post, user_infos, settings, logger
):
    """Test check_opa_authorization raises HTTPException on OPA internal server err."""

    class DummyResp:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    request = MagicMock()
    request.body = async_body
    request.url.path = "/test"
    request.method = "GET"

    mock_post.return_value = DummyResp()

    with pytest.raises(HTTPException) as exc:
        await auth.check_opa_authorization(
            request=request, user_infos=user_infos, settings=settings, logger=logger
        )
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@patch("requests.post")
async def test_check_opa_authorization_unexpected_status(
    mock_post, user_infos, settings, logger
):
    """Test check_opa_authorization raises HTTPException on unexpected status code."""

    class DummyResp:
        status_code = status.HTTP_418_IM_A_TEAPOT  # I'm a teapot (unexpected)

    request = MagicMock()
    request.body = async_body
    request.url.path = "/test"
    request.method = "GET"
    mock_post.return_value = DummyResp()
    with pytest.raises(HTTPException) as exc:
        await auth.check_opa_authorization(
            request=request, user_infos=user_infos, settings=settings, logger=logger
        )
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "unexpected response code" in exc.value.detail


@pytest.mark.asyncio
@patch("requests.post", side_effect=requests.Timeout)
async def test_check_opa_authorization_timeout(mock_post, user_infos, settings, logger):
    """Test that check_opa_authorization raises HTTPException on OPA timeout."""
    request = MagicMock()
    request.body = async_body
    request.url.path = "/test"
    request.method = "GET"
    with pytest.raises(HTTPException) as exc:
        await auth.check_opa_authorization(
            request=request, user_infos=user_infos, settings=settings, logger=logger
        )
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
@patch("fed_mgr.auth.check_opa_authorization")
async def test_check_authorization_opa(mock_check_opa, user_infos, settings, logger):
    """Test that check_authorization calls OPA authorization when mode is set to OPA."""
    settings.AUTHZ_MODE = auth.AuthorizationMethodsEnum.opa
    request = MagicMock()
    request.state.logger = logger
    mock_check_opa.return_value = None
    result = await auth.check_authorization(request, user_infos, settings)
    assert result is None


@pytest.mark.asyncio
async def test_check_authorization_none(user_infos, settings, logger):
    """Test that check_authorization does not raise when authorization mode is None."""
    settings.AUTHZ_MODE = None
    request = MagicMock()
    request.state.logger = logger
    # Should not raise
    result = await auth.check_authorization(request, user_infos, settings)
    assert result is None
