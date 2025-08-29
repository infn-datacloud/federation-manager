"""DB connection and creation details."""

from logging import Logger
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine, text

from fed_mgr.config import get_settings

settings = get_settings()

connect_args = {}
if settings.DB_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
engine = create_engine(settings.DB_URL, connect_args=connect_args, echo=settings.DB_ECO)


def create_db_and_tables(logger: Logger) -> Engine:
    """Connect to the database and create all tables defined in SQLModel metadata.

    Args:
        logger: Logger instance for logging database connection and table creation.

    Returns:
        The created database engine instance.

    """
    logger.info("Connecting to database and generating tables")
    SQLModel.metadata.create_all(engine)
    if engine.dialect.name == "sqlite":
        with engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_keys=ON"))
    return engine


def dispose_engine(logger: Logger) -> None:
    """Dispose of the database engine to free up resources.

    Args:
        logger: Logger instance for logging database disconnection.

    """
    logger.info("Disconnecting from database")
    engine.dispose()


def get_session():
    """Dependency generator that yields a SQLModel Session for database operations.

    Yields:
        Session: An active SQLModel session bound to the configured engine.

    """
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
