"""Entry point for the Federation-Manager web app."""
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from sqlite3 import Connection as SQLite3Connection
from typing import Any, Generator
from uuid import UUID

from fastapi import FastAPI
from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine, select

from fed_mng import models
from fed_mng.config import get_settings
from fed_mng.crud.users import change_role, create_user
from fed_mng.workflow.manager import engine as wf_engine

settings = get_settings()
sqlite3.register_adapter(UUID, lambda v: str(v))
sqlite3.register_converter("uuid", lambda s: UUID(s.decode("utf-8")))
sqlite3.register_adapter(dict, lambda v: json.dumps(v))
sqlite3.register_converter("json", lambda s: json.loads(s))
connect_args = {
    "check_same_thread": False,
    "detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
}
engine = create_engine(
    f"sqlite:///{settings.SQLITE_DB}", echo=True, connect_args=connect_args
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def initialize() -> None:
    with Session(engine) as session:
        for email, name in zip(settings.ADMIN_EMAIL_LIST, settings.ADMIN_NAME_LIST):
            statement = select(models.User).filter(models.User.email == email)
            user = session.exec(statement).first()
            if not user:
                user = create_user(session, models.UserCreate(name=name, email=email))
            statement = select(models.Admin).filter(models.Admin.id == user.id)
            admin = session.exec(statement).first()
            if not admin:
                change_role(session, user, models.Admin, True)
        # Upload processes
        for f in filter(lambda x: x.endswith(".bpmn"), os.listdir(settings.BPMN_DIR)):
            [fname, _] = f.split(".")
            wf_engine.add_spec(fname, [os.path.join(settings.BPMN_DIR, f)])


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    initialize()
    yield


def get_session() -> Generator[Session, Any, None]:
    with Session(engine) as session:
        yield session
