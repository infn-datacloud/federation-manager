"""Unit tests for fed_mgr.db module.

These tests cover:
- Table creation and logging in create_db_and_tables
- Engine disposal and logging in dispose_engine
- Session yielding in get_session
"""

from sqlmodel import Session, SQLModel

from fed_mgr.db import create_db_and_tables, dispose_engine, engine, get_session


class DummyLogger:
    """Dummy logger to capture log messages for assertions in tests."""

    def __init__(self):
        """Initialize the DummyLogger with an empty messages list."""
        self.messages = []

    def info(self, msg, *args):
        """Capture info log messages for assertions in tests."""
        self.messages.append((msg, args))


def test_create_db_and_tables_creates_tables(monkeypatch):
    """Test that `create_db_and_tables` calls SQLModel.metadata.create_all."""
    logger = DummyLogger()
    called = {}

    def fake_create_all(bind):
        called["bind"] = bind

    monkeypatch.setattr(SQLModel.metadata, "create_all", fake_create_all)
    result = create_db_and_tables(logger)
    assert called["bind"] is engine
    assert result is engine
    assert any("Connecting to database" in msg for msg, _ in logger.messages)


def test_dispose_engine_calls_engine_dispose(monkeypatch):
    """Test that dispose_engine calls engine.dispose and logs the disconnect."""
    logger = DummyLogger()
    called = {"dispose": False}

    def fake_dispose():
        called["dispose"] = True

    monkeypatch.setattr(engine, "dispose", fake_dispose)
    dispose_engine(logger)
    assert called["dispose"]
    assert any("Disconnecting from database" in msg for msg, _ in logger.messages)


def test_get_session_yields_session():
    """Test that get_session yields a Session instance bound to the engine."""
    gen = get_session()
    session = next(gen)
    assert isinstance(session, Session)
    # Clean up generator
    try:
        next(gen)
    except StopIteration:
        pass
