from datetime import date, datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import Base
from enums import (
    ProviderFederationStatus,
    ProviderFederationType,
    RequestType,
    ResourceUsageStatus,
    SLANegotiationStatus,
)

if TYPE_CHECKING:
    from provider import Provider
    from users import SiteAdmin, SiteTester, SLAModerator, UserGroupManager

REQ_ID_COL = "requests.id"
PROV_FED_ID_COL = "provider_federations.id"


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_date: Mapped[datetime] = mapped_column(nullable=False)
    update_date: Mapped[datetime] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(nullable=True)
    type: Mapped[RequestType] = mapped_column(nullable=False)

    __mapper_args__: ClassVar = {
        "polymorphic_identity": "provider_federations",
        "polymorphic_on": "type",
    }


class ProviderFederation(Request):
    __tablename__ = "provider_federations"

    id: Mapped[int] = mapped_column(ForeignKey(REQ_ID_COL), primary_key=True)
    status: Mapped[ProviderFederationStatus] = mapped_column(
        nullable=False, default=ProviderFederationStatus.SUBMITTED
    )
    operation: Mapped[ProviderFederationType] = mapped_column(nullable=False)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("site_admins.id"), nullable=False)
    tester_id: Mapped[int] = mapped_column(ForeignKey("site_testers.id"), nullable=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"), nullable=False)

    issuer: Mapped["SiteAdmin"] = relationship(back_populates="submitted_requests")
    tester: Mapped["SiteTester"] = relationship(back_populates="assigned_requests")
    provider: Mapped["Provider"] = relationship(back_populates="mentioning_requests")

    __mapper_args__: ClassVar = {
        "polymorphic_identity": RequestType.PROVIDER_FEDERATION,
        "polymorphic_on": "operation",
    }


class CreateProvider(ProviderFederation):
    __tablename__ = "create_providers"

    id: Mapped[int] = mapped_column(ForeignKey(PROV_FED_ID_COL), primary_key=True)

    __mapper_args__: ClassVar = {"polymorphic_identity": ProviderFederationType.CREATE}


class UpdateProvider(ProviderFederation):
    __tablename__ = "update_providers"

    id: Mapped[int] = mapped_column(ForeignKey(PROV_FED_ID_COL), primary_key=True)

    __mapper_args__: ClassVar = {"polymorphic_identity": ProviderFederationType.UPDATE}


class DeleteProvider(ProviderFederation):
    __tablename__ = "delete_providers"

    id: Mapped[int] = mapped_column(ForeignKey(PROV_FED_ID_COL), primary_key=True)

    __mapper_args__: ClassVar = {"polymorphic_identity": ProviderFederationType.DELETE}


class ResourceUsage(Request):
    __tablename__ = "resource_usages"

    id: Mapped[int] = mapped_column(ForeignKey(REQ_ID_COL), primary_key=True)
    status: Mapped[ResourceUsageStatus] = mapped_column(
        nullable=False, default=ResourceUsageStatus.SUBMITTED
    )
    preferred_sites: Mapped[str] = mapped_column(nullable=True)
    preferred_locations: Mapped[str] = mapped_column(nullable=True)
    preferred_identity_providers: Mapped[str] = mapped_column(nullable=True)
    preferred_start_date: Mapped[date] = mapped_column(nullable=True)
    preferred_end_date: Mapped[date] = mapped_column(nullable=True)
    issuer_id: Mapped[int] = mapped_column(
        ForeignKey("user_group_managers.id"), nullable=False
    )
    moderator_id: Mapped[int] = mapped_column(
        ForeignKey("sla_moderators.id"), nullable=True
    )

    issuer: Mapped["UserGroupManager"] = relationship(
        back_populates="submitted_requests"
    )
    moderator: Mapped["SLAModerator"] = relationship(back_populates="assigned_requests")

    __mapper_args__: ClassVar = {"polymorphic_identity": "resource_usages"}


class SLANegotiation(Request):
    __tablename__ = "sla_negotiations"

    id: Mapped[int] = mapped_column(ForeignKey(REQ_ID_COL), primary_key=True)
    status: Mapped[SLANegotiationStatus] = mapped_column(
        nullable=False, default=SLANegotiationStatus.SUBMITTED
    )

    __mapper_args__: ClassVar = {"polymorphic_identity": "sla_negotiations"}
