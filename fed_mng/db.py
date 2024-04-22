"""Entry point for the Federation-Manager web app."""
from contextlib import asynccontextmanager
from typing import Any, Generator

from fastapi import FastAPI
from sqlmodel import Session, SQLModel, create_engine, select

from fed_mng import models
from fed_mng.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False}
engine = create_engine(
    f"sqlite:///{settings.SQLITE_DB}", echo=True, connect_args=connect_args
)


def initialize() -> None:
    with Session(engine) as session:
        for email, name in zip(settings.ADMIN_EMAIL_LIST, settings.ADMIN_NAME_LIST):
            statement = select(models.User).filter(models.User.email == email)
            user: models.User = session.exec(statement).first()
            if not user:
                user = models.User(name=name, email=email)
                session.add(user)
                session.commit()
            else:
                statement = select(models.Admin).filter(models.Admin.id == user.id)
                admin: models.Admin = session.exec(statement).first()
                if not admin:
                    admin = models.Admin(id=user.id)
                    session.add(admin)
                    session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, Any, None]:
    SQLModel.metadata.create_all(engine)
    initialize()
    yield


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session
