"""Logger modules."""

import logging

from fed_mgr.config import LogLevelEnum, get_settings


def get_logger(
    name: str = "fed-mgr-api", log_level: LogLevelEnum | None = None
) -> logging.Logger:
    """Create and configure a logger for the fed-mgr API service.

    The logger outputs log messages to the console with a detailed format including
    timestamp, log level, logger name, process and thread information, and the message.
    The log level is set based on the application settings.

    Args:
        name: Name of the logger. Defaults to "fed-mgr-api".
        log_level (LogLevelEnum):  Log level for the logger. Defaults to the application
            settings.

    Returns:
        logging.Logger: The configured logger instance.

    """
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s "
        + "[%(processName)s: %(process)d - %(threadName)s: %(thread)d] "
        + "%(message)s"
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level=log_level or get_settings().LOG_LEVEL)
    logger.addHandler(stream_handler)

    return logger
