from typing import TYPE_CHECKING, ClassVar, List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import Base

if TYPE_CHECKING:
    from requests import ProviderFederation, ResourceUsage

USER_ID_COL = "users.id"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)

    __mapper_args__: ClassVar = {"polymorphic_identity": "users"}


class Admin(User):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(ForeignKey(USER_ID_COL), primary_key=True)

    __mapper_args__: ClassVar = {"polymorphic_identity": "admins"}


class SiteAdmin(User):
    __tablename__ = "site_admins"

    id: Mapped[int] = mapped_column(ForeignKey(USER_ID_COL), primary_key=True)

    submitted_requests: Mapped[List["ProviderFederation"]] = relationship(
        back_populates="issuer"
    )

    __mapper_args__: ClassVar = {"polymorphic_identity": "site_admins"}


class SiteTester(User):
    __tablename__ = "site_testers"

    id: Mapped[int] = mapped_column(ForeignKey(USER_ID_COL), primary_key=True)

    assigned_requests: Mapped[List["ProviderFederation"]] = relationship(
        back_populates="tester"
    )

    __mapper_args__: ClassVar = {"polymorphic_identity": "site_testers"}


class SLAModerator(User):
    __tablename__ = "sla_moderators"

    id: Mapped[int] = mapped_column(ForeignKey(USER_ID_COL), primary_key=True)

    assigned_requests: Mapped[List["ResourceUsage"]] = relationship(
        back_populates="moderator"
    )

    __mapper_args__: ClassVar = {"polymorphic_identity": "sla_moderators"}


class UserGroupManager(User):
    __tablename__ = "user_group_managers"

    id: Mapped[int] = mapped_column(ForeignKey(USER_ID_COL), primary_key=True)

    submitted_requests: Mapped[List["ResourceUsage"]] = relationship(
        back_populates="issuer"
    )

    __mapper_args__: ClassVar = {"polymorphic_identity": "user_group_managers"}
