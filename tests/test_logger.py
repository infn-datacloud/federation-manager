"""Unit tests for fed_mgr.logger module.

These tests cover:
- Logger creation and configuration in get_logger
- Log level setting
- Log message formatting
"""

import logging
import re

from fed_mgr.logger import get_logger


class DummySettings:
    """Dummy settings class for testing logger configuration."""

    def __init__(self, log_level):
        """Initialize DummySettings with a log level."""
        self.LOG_LEVEL = log_level


def test_get_logger_returns_logger_and_sets_level(monkeypatch):
    """Test that get_logger returns a logger with the correct name and log level."""
    settings = DummySettings(logging.WARNING)
    logger = get_logger(settings)
    assert isinstance(logger, logging.Logger)
    assert logger.name == "fed-mgr-api"
    assert logger.level == logging.WARNING


def test_get_logger_adds_stream_handler_and_formatter(monkeypatch):
    """Test that get_logger adds a StreamHandler with the correct formatter."""
    settings = DummySettings(logging.INFO)
    logger = get_logger(settings)
    # There should be at least one StreamHandler
    handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert handlers, "No StreamHandler attached to logger"
    # The formatter should match the expected format
    formatter = handlers[0].formatter
    log_record = logging.LogRecord(
        name="fed-mgr-api",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(log_record)
    # Check for expected fields in the formatted log
    assert re.search(r"\d{4}-\d{2}-\d{2}", formatted)  # Date
    assert "INFO" in formatted
    assert "fed-mgr-api" in formatted
    assert "Test message" in formatted
    assert "processName" in formatter._fmt
    assert "threadName" in formatter._fmt
