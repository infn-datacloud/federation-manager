from datetime import date, datetime
from typing import Optional

from app.provider.enum import ProviderStatus, ProviderType
from sqlmodel import Field, Relationship, SQLModel

from enums import (
    ProviderFederationStatus,
    ProviderFederationType,
    ResourceUsageStatus,
    SLANegotiationStatus,
    SLAStatus,
)

PROV_ID_COL = "providers.id"
PROV_FED_ID_COL = "provider_federations.id"
QUOTA_ID_COL = "quotas.id"
REQ_ID_COL = "requests.id"
USER_ID_COL = "users.id"


class Administrates(SQLModel, table=True):
    __tablename__ = "administrates"

    provider_id: int = Field(foreign_key=PROV_ID_COL, primary_key=True)
    site_admin_id: int = Field(foreign_key="site_admins.id", primary_key=True)


class Trusts(SQLModel, table=True):
    __tablename__ = "trusts"

    idp_name: str = Field(nullable=False)
    protocol: str = Field(nullable=False)
    provider_id: int = Field(foreign_key=PROV_ID_COL, primary_key=True)
    identity_provider_id: int = Field(
        foreign_key="identity_providers.id", primary_key=True
    )

    provider: "Provider" = Relationship(back_populates="trusted_identity_providers")
    identity_providers: "IdentityProvider" = Relationship(
        back_populates="authorized_providers"
    )


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
    providers: list["Provider"] = Relationship(
        back_populates="site_admins", link_model=Administrates
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
    provider_id: int = Field(foreign_key=PROV_ID_COL, nullable=False)

    issuer: "SiteAdmin" = Relationship(back_populates="submitted_requests")
    tester: "SiteTester" = Relationship(back_populates="assigned_requests")
    provider: "Provider" = Relationship(back_populates="mentioning_requests")


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
    negotiations: list["SLANegotiation"] = Relationship(back_populates="parent_request")
    tot_block_storage_quota: "TotBlockStorageQuota" = Relationship(
        back_populates="mentioning_request"
    )
    tot_compute_quota: "TotComputeQuota" = Relationship(
        back_populates="mentioning_request"
    )
    tot_network_quota: "TotNetworkQuota" = Relationship(
        back_populates="mentioning_request"
    )
    user_block_storage_quota: "UserBlockStorageQuota" = Relationship(
        back_populates="mentioning_request"
    )
    user_compute_quota: "UserComputeQuota" = Relationship(
        back_populates="mentioning_request"
    )
    user_network_quota: "UserNetworkQuota" = Relationship(
        back_populates="mentioning_request"
    )


class SLANegotiation(RequestBase, table=True):
    __tablename__ = "sla_negotiations"

    status: SLANegotiationStatus = Field(
        nullable=False, default=SLANegotiationStatus.SUBMITTED
    )
    provider_id: int = Field(foreign_key=PROV_ID_COL, nullable=False)
    parent_request_id: int = Field(foreign_key="resource_usages.id", nullable=False)
    sla_id: int = Field(foreign_key="slas.id", nullable=False)

    provider: "Provider" = Relationship(back_populates="negotiations")
    parent_request: "ResourceUsage" = Relationship(back_populates="negotiations")
    sla: "SLA" = Relationship(back_populates="negotiation")


class Provider(SQLModel, table=True):
    __tablename__ = "providers"

    id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    type: ProviderType = Field(nullable=False)
    auth_url: str = Field(nullable=False)
    is_public: bool = Field(default=False)
    status: ProviderStatus = Field(nullable=False, default=ProviderStatus.ACTIVE)
    # vol_types: str = Field(nullable=False)
    description: str = Field(nullable=True)
    image_tags: str = Field(nullable=True)
    network_tags: str = Field(nullable=True)
    next_version_id: int | None = Field(foreign_key=PROV_ID_COL, nullable=True)
    # TODO evaluate to use prev_version_id instead of next_version_id

    mentioning_requests: list["ProviderFederation"] = Relationship(
        back_populates="provider"
    )
    prev_version: Optional["Provider"] = Relationship(back_populates="next_version")
    next_version: Optional["Provider"] = Relationship(
        back_populates="prev_version",
        sa_relationship_kwargs={"remote_side": "Provider.id"},
    )
    regions: list["Region"] = Relationship(back_populates="provider")
    site_admins: list["SiteAdmin"] = Relationship(
        back_populates="providers", link_model=Administrates
    )
    trusted_identity_providers: list["Trusts"] = Relationship(back_populates="provider")
    negotiations: list["SLANegotiation"] = Relationship(back_populates="provider")


class Region(SQLModel, table=True):
    __tablename__ = "regions"

    id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    description: str = Field(nullable=True)
    provider_id: int = Field(foreign_key=PROV_ID_COL, nullable=False)
    location_id: int | None = Field(foreign_key="locations.id", nullable=True)

    provider: "Provider" = Relationship(back_populates="regions")
    location: "Location" = Relationship(back_populates="regions")


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: int = Field(primary_key=True)
    site: str = Field(nullable=False)
    country: str = Field(nullable=False)
    description: str = Field(nullable=True)
    latitude: float = Field(nullable=True)
    longitude: float = Field(nullable=True)

    regions: list["Region"] = Relationship(back_populates="location")


class IdentityProvider(SQLModel, table=True):
    __tablename__ = "identity_providers"

    id: int = Field(primary_key=True)
    endpoint: str = Field(nullable=False)
    description: str = Field(nullable=True)

    authorized_providers: list["Trusts"] = Relationship(
        back_populates="identity_providers"
    )


class Quota(SQLModel):
    id: int | None = Field(primary_key=True)
    mentioning_request_id: int = Field(foreign_key="resource_usages.id", nullable=False)
    sla_id: int | None = Field(foreign_key="slas.id", nullable=False)


class BlockStorageQuota(Quota):
    gigabytes: int | None = Field(nullable=True)
    per_volume_gigabytes: int | None = Field(nullable=True)
    volumes: int | None = Field(nullable=True)


class TotBlockStorageQuota(BlockStorageQuota, table=True):
    __tablename__ = "tot_block_storage_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="tot_block_storage_quota"
    )
    sla: "SLA" = Relationship(back_populates="tot_block_storage_quota")


class UserBlockStorageQuota(BlockStorageQuota, table=True):
    __tablename__ = "user_block_storage_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="user_block_storage_quota"
    )
    sla: "SLA" = Relationship(back_populates="user_block_storage_quota")


class ComputeQuota(Quota):
    cores: int | None = Field(nullable=True)
    instances: int | None = Field(nullable=True)
    ram: int | None = Field(nullable=True)


class TotComputeQuota(ComputeQuota, table=True):
    __tablename__ = "tot_compute_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="tot_compute_quota"
    )
    sla: "SLA" = Relationship(back_populates="tot_compute_quota")


class UserComputeQuota(Quota, table=True):
    __tablename__ = "user_compute_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="user_compute_quota"
    )
    sla: "SLA" = Relationship(back_populates="user_compute_quota")


class NetworkQuota(Quota):
    networks: int | None = Field(nullable=True)
    ports: int | None = Field(nullable=True)
    public_ips: int | None = Field(nullable=True)
    security_groups: int | None = Field(nullable=True)
    security_groups_rules: int | None = Field(nullable=True)


class TotNetworkQuota(NetworkQuota, table=True):
    __tablename__ = "tot_network_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="tot_network_quota"
    )
    sla: "SLA" = Relationship(back_populates="tot_network_quota")


class UserNetworkQuota(NetworkQuota, table=True):
    __tablename__ = "user_network_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="user_network_quota"
    )
    sla: "SLA" = Relationship(back_populates="user_network_quota")


class SLA(SQLModel, table=True):
    __tablename__ = "slas"

    id: int | None = Field(primary_key=True)
    doc_uuid: str | None = Field(nullable=True)
    start_date: date = Field(nullable=False)
    end_date: date = Field(nullable=False)
    status: SLAStatus = Field(nullable=False, default=SLAStatus.DISCUSSING)

    negotiation: "SLANegotiation" = Relationship(back_populates="sla")
    tot_block_storage_quota: "TotBlockStorageQuota" = Relationship(back_populates="sla")
    tot_compute_quota: "TotComputeQuota" = Relationship(back_populates="sla")
    tot_network_quota: "TotNetworkQuota" = Relationship(back_populates="sla")
    user_block_storage_quota: "UserBlockStorageQuota" = Relationship(
        back_populates="sla"
    )
    user_compute_quota: "UserComputeQuota" = Relationship(back_populates="sla")
    user_network_quota: "UserNetworkQuota" = Relationship(back_populates="sla")


# TODO Add "sa_relationship_kwargs={'uselist': False}" to 1-1 relationship
