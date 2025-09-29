"""Logger modules."""

import logging

from fed_mgr.config import Settings


def get_logger(settings: Settings, name: str | None = None) -> logging.Logger:
    """Create and configure a logger for the fed-mgr API service.

    The logger outputs log messages to the console with a detailed format including
    timestamp, log level, logger name, process and thread information, and the message.
    The log level is set based on the application settings.

    Args:
        settings: The application settings instance containing the log level.

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

    logger = logging.getLogger(name if name is not None else "fed-mgr-api")
    logger.setLevel(level=settings.LOG_LEVEL)
    logger.addHandler(stream_handler)

    return logger
