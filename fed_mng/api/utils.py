from typing import Sequence, Type

from sqlmodel import Session, select

from fed_mng.models import (
    Admin,
    Query,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    User,
    UserCreate,
    UserGroupManager,
    UserQuery,
)


def change_role(
    session: Session,
    user: User,
    role: Type[Admin]
    | Type[SiteAdmin]
    | Type[SiteTester]
    | Type[SLAModerator]
    | Type[UserGroupManager],
    enable_role: bool | None,
) -> User:
    if enable_role is not None:
        user_role = session.exec(select(role).filter(role.id == user.id)).first()
        if enable_role and user_role is None:
            item = role(id=user.id)
            session.add(item)
            session.commit()
        elif not enable_role and user_role is not None:
            session.delete(user_role)
            session.commit()
    return user


def create_user(session: Session, user: UserCreate) -> User:
    item = User(**user.model_dump())
    session.add(item)
    session.commit()
    return item


def get_users(session: Session, user: UserQuery, query: Query) -> Sequence[User]:
    statement = select(User)
    for k, v in user.model_dump(exclude_none=True).items():
        statement = statement.filter(getattr(User, k) == v)
    statement = statement.offset(query.offset).limit(query.size)

    if query.sort is not None:
        reverse = query.sort.startswith("-")
        sort_attr = query.sort[1:] if reverse else query.sort
        sort_rule = getattr(User, sort_attr)
        if reverse:
            sort_rule = sort_rule.desc()
        statement = statement.order_by(sort_rule)

    return session.exec(statement).all()
