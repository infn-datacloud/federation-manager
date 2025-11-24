"""DB connection and creation details."""

import collections.abc
import typing

import sqlalchemy
import sqlmodel
from fastapi import Depends
from sqlmodel import Session, SQLModel

from fed_mgr.config import get_settings
from fed_mgr.logger import get_logger


class DBHandlerMeta(type):
    """Singleton metaclass for DBHandler."""

    _instances: typing.ClassVar = {}

    def __call__(cls, *args, **kwargs):
        """Return the singleton instance of DBHandler."""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@typing.final
class DBHandler(metaclass=DBHandlerMeta):
    """Class for managing database connections."""

    def __init__(self) -> None:
        """Initialize the DBHandler."""
        self._logger = get_logger(__class__.__name__)
        self._settings = get_settings()
        self._engine = self.__create_engine()
        self._initialized = False

    def __del__(self) -> None:
        """Disconnect from the database."""
        self._logger.info("Disconnecting from database")
        self._engine.dispose()

    def __create_engine(self) -> sqlalchemy.Engine:
        """Create the database engine."""
        connect_args = {}
        if self._settings.DB_URL.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        return sqlmodel.create_engine(
            self._settings.DB_URL,
            connect_args=connect_args,
            echo=self._settings.DB_ECO,
        )

    def initialize_db(self) -> None:
        """Initialize the database."""
        assert self._engine is not None
        if self._initialized:
            self._logger.warning("Database already initialized")
            return

        self._logger.info("Connecting to database and generating tables")
        SQLModel.metadata.create_all(self._engine)
        if self._engine.dialect.name == "sqlite":
            with self._engine.connect() as connection:
                connection.execute(sqlmodel.text("PRAGMA foreign_keys=ON"))

    def get_engine(self) -> sqlalchemy.Engine:
        """Return the database engine."""
        return self._engine

    @classmethod
    def get_dialect(cls) -> str:
        """Return the database dialect."""
        instance = cls()
        dialect_name = instance._engine.dialect.name
        if dialect_name is None or dialect_name == "":
            raise ValueError("Dialect name not set")
        return dialect_name


def get_session() -> collections.abc.Generator[Session, typing.Any, None]:
    """Dependency generator that yields a SQLModel Session for database operations.

    Yields:
        Session: An active SQLModel session bound to the configured engine.

    """
    engine = DBHandler().get_engine()
    with Session(engine) as session:
        yield session


SessionDep = typing.Annotated[Session, Depends(get_session)]
