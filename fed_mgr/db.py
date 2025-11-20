"""DB connection and creation details."""

import typing
from typing import Annotated

import sqlmodel
from fastapi import Depends
from sqlmodel import Session, SQLModel

from fed_mgr.config import get_settings
from fed_mgr.logger import get_logger


class DBHandlerMeta(type):
    """Singleton metaclass for DBHandler."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Return the singleton instance of DBHandler."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@typing.final
class DBHandler(metaclass=DBHandlerMeta):
    """Class for managing database connections."""

    def __init__(self):
        """Initialize the DBHandler."""
        self._logger = get_logger(__class__.__name__)
        self._settings = get_settings()
        self._engine = self.__create_engine()
        self.__initialize_db()

    def __del__(self):
        """Disconnect from the database."""
        self._logger.info("Disconnecting from database")
        self._engine.dispose()

    def __create_engine(self):
        """Create the database engine."""
        connect_args = {}
        if self._settings.DB_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        return sqlmodel.create_engine(
            self._settings.DB_URL,
            connect_args=connect_args,
            echo=self._settings.DB_ECO,
        )

    def __initialize_db(self):
        """Initialize the database."""
        assert self._engine is not None
        self._logger.info("Connecting to database and generating tables")
        SQLModel.metadata.create_all(self._engine)
        if self._engine.dialect.name == "sqlite":
            with self._engine.connect() as connection:
                connection.execute(sqlmodel.text("PRAGMA foreign_keys=ON"))

    def get_engine(self):
        """Return the database engine."""
        return self._engine


def get_session():
    """Dependency generator that yields a SQLModel Session for database operations.

    Yields:
        Session: An active SQLModel session bound to the configured engine.

    """
    engine = DBHandler().get_engine()
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
