"""Tests for the fed_mgr.__init__ module."""

from unittest import mock

import pytest

from fed_mgr import main


@pytest.mark.asyncio
async def test_lifespan_calls_dependencies(mock_logger):
    """Test that `lifespan` correctly calls its dependencies.

    This test verifies:
    - The logger is obtained and returned in the context.
    - The `configure_flaat` and `create_db_and_tables` functions are called with the
        expected arguments.
    - The `dispose_engine` function is not called until the context is exited.
    - Upon exiting the context, `dispose_engine` is called with the logger.

    Mocks are used to patch dependencies and assert their invocation.
    """
    # Patch dependencies
    with (
        mock.patch.object(main, "get_logger") as mock_get_logger,
        mock.patch.object(main, "configure_flaat") as mock_configure_flaat,
        mock.patch.object(main, "create_db_and_tables") as mock_create_db_and_tables,
        mock.patch.object(main, "dispose_engine") as mock_dispose_engine,
        mock.patch("fed_mgr.v1.users.crud.get_users", return_value=([], 0)),
    ):
        mock_get_logger.return_value = mock_logger

        # Create a dummy FastAPI app
        dummy_app = mock.Mock()

        # Use the async context manager
        cm = main.lifespan(dummy_app)
        # __aenter__ yields the dict
        result = await cm.__aenter__()
        assert result == {"logger": mock_logger}

        # Check that dependencies were called as expected
        mock_get_logger.assert_called_once_with(main.settings)
        mock_configure_flaat.assert_called_once_with(main.settings, mock_logger)
        mock_create_db_and_tables.assert_called_once_with(mock_logger)
        mock_dispose_engine.assert_not_called()  # Not called until exit

        # Now exit the context and check dispose_engine is called
        await cm.__aexit__(None, None, None)
        mock_dispose_engine.assert_called_once_with(mock_logger)


@pytest.mark.asyncio
async def test_lifespan_calls_create_fake_user_when_authn_mode_none(monkeypatch):
    """Test lifespan calls create_fake_user when AUTHN_MODE is None."""
    fake_logger = mock.Mock()
    fake_engine = mock.Mock()
    fake_settings = mock.Mock()
    fake_settings.AUTHN_MODE = None
    fake_session_ctx = mock.MagicMock()
    fake_session = mock.Mock()
    monkeypatch.setattr(main, "get_logger", lambda s: fake_logger)
    monkeypatch.setattr(main, "configure_flaat", lambda s, log: None)
    monkeypatch.setattr(main, "create_db_and_tables", lambda log: fake_engine)
    monkeypatch.setattr(main, "dispose_engine", lambda log: None)
    monkeypatch.setattr(main, "settings", fake_settings)
    monkeypatch.setattr(main, "Session", lambda e: fake_session_ctx)
    fake_session_ctx.__enter__.return_value = fake_session
    fake_session_ctx.__exit__.return_value = None
    called = {"create": False}

    async def async_fake_start_kafka_listeners(s, log):
        return mock.Mock()

    monkeypatch.setattr(main, "start_kafka_listeners", async_fake_start_kafka_listeners)

    async def async_fake_stop_kafka_listeners(tasks, log):
        return None

    monkeypatch.setattr(main, "stop_kafka_listeners", async_fake_stop_kafka_listeners)

    def fake_create_fake_user(s):
        called["create"] = True

    monkeypatch.setattr(main, "create_fake_user", fake_create_fake_user)
    monkeypatch.setattr(main, "delete_fake_user", lambda s: None)
    cm = main.lifespan(mock.Mock())
    await cm.__aenter__()
    assert called["create"] is True
    await cm.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_lifespan_calls_delete_fake_user_when_authn_mode_set(monkeypatch):
    """Test lifespan calls delete_fake_user when AUTHN_MODE is not None."""
    fake_logger = mock.Mock()
    fake_engine = mock.Mock()
    fake_settings = mock.Mock()
    fake_settings.AUTHN_MODE = "not_none"
    fake_session_ctx = mock.MagicMock()
    fake_session = mock.Mock()
    monkeypatch.setattr(main, "get_logger", lambda s: fake_logger)
    monkeypatch.setattr(main, "configure_flaat", lambda s, log: None)
    monkeypatch.setattr(main, "create_db_and_tables", lambda log: fake_engine)
    monkeypatch.setattr(main, "dispose_engine", lambda log: None)
    monkeypatch.setattr(main, "settings", fake_settings)
    monkeypatch.setattr(main, "Session", lambda e: fake_session_ctx)
    fake_session_ctx.__enter__.return_value = fake_session
    fake_session_ctx.__exit__.return_value = None
    called = {"delete": False}

    async def async_fake_start_kafka_listeners(s, log):
        return mock.Mock()

    monkeypatch.setattr(main, "start_kafka_listeners", async_fake_start_kafka_listeners)

    async def async_fake_stop_kafka_listeners(tasks, log):
        return None

    monkeypatch.setattr(main, "stop_kafka_listeners", async_fake_stop_kafka_listeners)

    def fake_delete_fake_user(s):
        called["delete"] = True

    monkeypatch.setattr(main, "create_fake_user", lambda s: None)
    monkeypatch.setattr(main, "delete_fake_user", fake_delete_fake_user)
    cm = main.lifespan(mock.Mock())
    await cm.__aenter__()
    assert called["delete"] is True
    await cm.__aexit__(None, None, None)
