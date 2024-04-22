from typing import Type

from sqlmodel import Session, select

from fed_mng.models import (
    Admin,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    User,
    UserGroupManager,
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
) -> bool:
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
