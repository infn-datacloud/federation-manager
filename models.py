from datetime import date, datetime
import json
from pydantic import validator

from sqlmodel import Field, Relationship, SQLModel

from enums import (
    ProviderFederationStatus,
    ProviderFederationType,
    RequestType,
    ResourceUsageStatus,
    SLANegotiationStatus,
)

USER_ID_COL = "users.id"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(primary_key=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)


class Admin(SQLModel, table=True):
    __tablename__ = "admins"

    id: int = Field(foreign_key=USER_ID_COL, primary_key=True)


class SiteAdmin(SQLModel, table=True):
    __tablename__ = "site_admins"

    id: int = Field(foreign_key=USER_ID_COL, primary_key=True)

    submitted_requests: list["ProviderFederation"] = Relationship(
        back_populates="issuer"
    )


class SiteTester(SQLModel, table=True):
    __tablename__ = "site_testers"

    id: int = Field(foreign_key=USER_ID_COL, primary_key=True)

    assigned_requests: list["ProviderFederation"] = Relationship(
        back_populates="tester"
    )


class SLAModerator(SQLModel, table=True):
    __tablename__ = "sla_moderators"

    id: int = Field(foreign_key=USER_ID_COL, primary_key=True)

    assigned_requests: list["ResourceUsage"] = Relationship(back_populates="moderator")


class UserGroupManager(SQLModel, table=True):
    __tablename__ = "user_group_managers"

    id: int = Field(foreign_key=USER_ID_COL, primary_key=True)

    submitted_requests: list["ResourceUsage"] = Relationship(back_populates="issuer")


REQ_ID_COL = "requests.id"
PROV_FED_ID_COL = "provider_federations.id"


class RequestBase(SQLModel):
    id: int | None = Field(primary_key=True)
    issue_date: datetime = Field(nullable=False)
    update_date: datetime = Field(nullable=False)
    message: str = Field(nullable=True)


class ProviderFederation(RequestBase, table=True):
    __tablename__ = "provider_federations"

    status: ProviderFederationStatus = Field(
        nullable=False, default=ProviderFederationStatus.SUBMITTED
    )
    operation: ProviderFederationType = Field(nullable=False)
    issuer_id: int = Field(foreign_key="site_admins.id", nullable=False)
    tester_id: int = Field(foreign_key="site_testers.id", nullable=True)
    # provider_id: int = Field(foreign_key="providers.id", nullable=False)

    issuer: "SiteAdmin" = Relationship(back_populates="submitted_requests")
    tester: "SiteTester" = Relationship(back_populates="assigned_requests")
    # provider: "Provider" = Relationship(back_populates="mentioning_requests")


# class CreateProvider(ProviderFederation):
#     __tablename__ = "create_providers"

#     id: int] = Field(ForeignKey(PROV_FED_ID_COL), primary_key=True)

#     __mapper_args__: ClassVar = {"polymorphic_identity": ProviderFederationType.CREATE}


# class UpdateProvider(ProviderFederation):
#     __tablename__ = "update_providers"

#     id: int] = Field(ForeignKey(PROV_FED_ID_COL), primary_key=True)

#     __mapper_args__: ClassVar = {"polymorphic_identity": ProviderFederationType.UPDATE}


# class DeleteProvider(ProviderFederation):
#     __tablename__ = "delete_providers"

#     id: int] = Field(ForeignKey(PROV_FED_ID_COL), primary_key=True)

#     __mapper_args__: ClassVar = {"polymorphic_identity": ProviderFederationType.DELETE}


class ResourceUsage(RequestBase, table=True):
    __tablename__ = "resource_usages"

    status: ResourceUsageStatus = Field(
        nullable=False, default=ResourceUsageStatus.SUBMITTED
    )
    preferred_sites: str = Field(nullable=True)
    preferred_locations: str = Field(nullable=True)
    preferred_identity_providers: str = Field(nullable=True)
    preferred_start_date: date = Field(nullable=True)
    preferred_end_date: date = Field(nullable=True)
    issuer_id: int = Field(foreign_key="user_group_managers.id", nullable=False)
    moderator_id: int = Field(foreign_key="sla_moderators.id", nullable=True)

    issuer: "UserGroupManager" = Relationship(back_populates="submitted_requests")
    moderator: "SLAModerator" = Relationship(back_populates="assigned_requests")


class SLANegotiation(RequestBase, table=True):
    __tablename__ = "sla_negotiations"

    status: SLANegotiationStatus = Field(
        nullable=False, default=SLANegotiationStatus.SUBMITTED
    )
