"""Logger modules."""

import logging
from enum import Enum


class LogLevelEnum(int, Enum):
    """Enumeration of supported logging levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def get_logger(log_level: LogLevelEnum) -> logging.Logger:
    """Create and configure a logger for the fed-mgr API service.

    The logger outputs log messages to the console with a detailed format including
    timestamp, log level, logger name, process and thread information, and the message.
    The log level is set based on the application settings.

    Args:
        log_level (LogLevelEnum): Loggging level.

    Returns:
        logging.Logger: The configured logger instance.

    """
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s "
        "[%(processName)s: %(process)d - %(threadName)s: %(thread)d] "
        "%(message)s"
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger("fed-mgr-api")
    logger.setLevel(level=log_level)
    logger.addHandler(stream_handler)

    return logger
