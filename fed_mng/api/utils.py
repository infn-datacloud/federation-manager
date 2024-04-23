"""Utilities for the users endpoints."""
from typing import Sequence, Type

from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from fed_mng.models import (
    Admin,
    Query,
    RoleQuery,
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
    """Change user role.

    If `enable_role` is None, do nothing. Otherwise if `enable_role` is true and the
    user does not alreay have this role, give it. On the other hand if `enable_role`
    is false and the user already has that role, revoke it.

    Return the user updated instance.
    """

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


def filter_role(
    statement: SelectOfScalar[User],
    role: Type[Admin]
    | Type[SiteAdmin]
    | Type[SiteTester]
    | Type[SLAModerator]
    | Type[UserGroupManager],
    match_role: bool | None,
) -> SelectOfScalar[User]:
    """Filter user by role.

    If `match_role` is None, do nothing. Otherwise if `match_role` is true, add to the
    statement a join condition to match users having that role. On the other hand if
    `match_role` is false, update the statement to exclude users having that role.

    Return the updated statement.
    """

    if match_role is True:
        return statement.join(role)
    elif match_role is False:
        return statement.join(role, isouter=True).filter(role.id == None)  # noqa: E711


def create_user(session: Session, user: UserCreate) -> User:
    """Create a user."""
    item = User(**user.model_dump())
    session.add(item)
    session.commit()
    return item


def retrieve_users(
    session: Session, user: UserQuery, query: Query, role: RoleQuery
) -> Sequence[User]:
    """Get list of users.

    If specified, filter by user attributes and roles. Paginate resulting list.
    Sort the list by the given attribute (both ascending or descending order).

    Return the list of filtered and sorted items.
    """
    statement = select(User)
    for k, v in user.model_dump(exclude_none=True).items():
        statement = statement.filter(getattr(User, k) == v)

    statement = filter_role(statement, Admin, role.is_admin)
    statement = filter_role(statement, SiteAdmin, role.is_site_admin)
    statement = filter_role(statement, SiteTester, role.is_site_tester)
    statement = filter_role(statement, SLAModerator, role.is_sla_moderator)
    statement = filter_role(statement, UserGroupManager, role.is_user_group_manager)

    statement = statement.offset(query.offset).limit(query.size)

    if query.sort is not None:
        reverse = query.sort.startswith("-")
        sort_attr = query.sort[1:] if reverse else query.sort
        sort_rule = getattr(User, sort_attr)
        if reverse:
            sort_rule = sort_rule.desc()
        statement = statement.order_by(sort_rule)

    return session.exec(statement).all()
