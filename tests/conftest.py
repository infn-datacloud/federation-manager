from typing import Any, Generator

import pytest
from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine

from fed_mng.models import (
    SLA,
    Provider,
    Region,
    ResourceUsage,
    SLANegotiation,
    SiteAdmin,
    SLAModerator,
    User,
    UserGroupManager,
)
from tests.item_data import (
    provider_dict,
    region_dict,
    request_dict,
    sla_dict,
    user_dict,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, Any, None]:
    """Define the database engine and create all tables."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine: Engine) -> Generator[Session, Any, None]:
    """yields a SQLAlchemy connection which is rollbacked after the test"""
    with Session(bind=db_engine) as session:
        yield session
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def db_user(db_session: Session) -> User:
    d = user_dict()
    user = User(**d)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def db_site_admin(db_session: Session, db_user: User) -> SiteAdmin:
    site_admin = SiteAdmin(id=db_user.id)
    db_session.add(site_admin)
    db_session.commit()
    db_session.refresh(site_admin)
    return site_admin


@pytest.fixture(scope="function")
def db_sla_moderator(db_session: Session, db_user: User) -> SLAModerator:
    sla_moderator = SLAModerator(id=db_user.id)
    db_session.add(sla_moderator)
    db_session.commit()
    db_session.refresh(sla_moderator)
    return sla_moderator


@pytest.fixture(scope="function")
def db_user_group_manager(db_session: Session, db_user: User) -> UserGroupManager:
    user_group_manager = UserGroupManager(id=db_user.id)
    db_session.add(user_group_manager)
    db_session.commit()
    db_session.refresh(user_group_manager)
    return user_group_manager


@pytest.fixture(scope="function")
def db_resource_usage_request(
    db_session: Session, db_user_group_manager: UserGroupManager
) -> ResourceUsage:
    res_use_req = ResourceUsage(**request_dict(), issuer=db_user_group_manager)
    db_session.add(res_use_req)
    db_session.commit()
    db_session.refresh(res_use_req)
    return res_use_req


@pytest.fixture(scope="function")
def db_provider(db_session: Session) -> Provider:
    data = provider_dict()
    db_provider = Provider(**data)
    db_session.add(db_provider)
    db_session.commit()
    db_session.refresh(db_provider)
    return db_provider


@pytest.fixture(scope="function")
def db_region(db_session: Session, db_provider: Provider) -> Region:
    data = region_dict()
    db_region = Region(**data, provider=db_provider)
    db_session.add(db_region)
    db_session.commit()
    db_session.refresh(db_region)
    return db_region


@pytest.fixture(scope="function")
def db_negotiation(
    db_session: Session, db_provider: Provider, db_resource_usage_request: ResourceUsage
) -> SLANegotiation:
    data = request_dict()
    db_negotiation = SLANegotiation(
        **data, parent_request=db_resource_usage_request, provider=db_provider
    )
    db_session.add(db_negotiation)
    db_session.commit()
    db_session.refresh(db_negotiation)
    return db_negotiation


@pytest.fixture(scope="function")
def db_sla(db_session: Session, db_negotiation: SLANegotiation) -> SLA:
    data = sla_dict()
    db_sla = SLA(**data, negotiation=db_negotiation)
    db_session.add(db_sla)
    db_session.commit()
    db_session.refresh(db_sla)
    return db_sla
