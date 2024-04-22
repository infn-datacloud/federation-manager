"""Entry point for the Federation-Manager web app."""
from contextlib import asynccontextmanager
from typing import Any, Generator

from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine

from fed_mng import models  # noqa: F401
from fed_mng.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False}
engine = create_engine(
    f"sqlite:///{settings.SQLITE_DB}", echo=True, connect_args=connect_args
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, Any, None]:
    SQLModel.metadata.create_all(engine)
    yield


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session
