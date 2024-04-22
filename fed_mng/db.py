"""Entry point for the Federation-Manager web app."""
from contextlib import asynccontextmanager
from typing import Any, Generator

from sqlmodel import Session, SQLModel, create_engine

connect_args = {"check_same_thread": False}
engine = create_engine("sqlite://", echo=True, connect_args=connect_args)


@asynccontextmanager
async def lifespan() -> None:
    print("here")
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session
