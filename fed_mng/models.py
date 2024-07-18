from datetime import date, datetime
from typing import Any, Optional

from fed_reg.provider.enum import ProviderStatus, ProviderType
from pydantic import validator
from sqlalchemy import func
from sqlmodel import Field, Relationship, SQLModel

from fed_mng.enums import (
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


class UserBase(SQLModel):
    name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(primary_key=True)


class UserCreate(UserBase):
    ...


class UserQuery(SQLModel):
    name: str | None = Field(nullable=True)
    email: str | None = Field(nullable=True)


class UserUpdate(UserQuery):
    ...


class RoleQuery(SQLModel):
    is_admin: bool | None = None
    is_site_admin: bool | None = None
    is_site_tester: bool | None = None
    is_sla_moderator: bool | None = None
    is_user_group_manager: bool | None = None


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
    message: str | None = Field(nullable=True)


class ProviderFederation(RequestBase, table=True):
    __tablename__ = "provider_federations"

    status: ProviderFederationStatus = Field(
        nullable=False, default=ProviderFederationStatus.SUBMITTED
    )
    operation: ProviderFederationType = Field(nullable=False)
    issuer_id: int = Field(foreign_key="site_admins.id", nullable=False)
    tester_id: int | None = Field(foreign_key="site_testers.id", nullable=True)
    provider_id: int = Field(foreign_key=PROV_ID_COL, nullable=False)

    issuer: "SiteAdmin" = Relationship(back_populates="submitted_requests")
    tester: Optional["SiteTester"] = Relationship(back_populates="assigned_requests")
    provider: "Provider" = Relationship(back_populates="mentioning_requests")


# class CreateProvider(ProviderFederation):
#     __tablename__ = "create_providers"

#     id: int = Field(ForeignKey(PROV_FED_ID_COL), primary_key=True)


# class UpdateProvider(ProviderFederation):
#     __tablename__ = "update_providers"

#     id: int = Field(ForeignKey(PROV_FED_ID_COL), primary_key=True)


# class DeleteProvider(ProviderFederation):
#     __tablename__ = "delete_providers"

#     id: int = Field(ForeignKey(PROV_FED_ID_COL), primary_key=True)


class ResourceUsage(RequestBase, table=True):
    __tablename__ = "resource_usages"

    status: ResourceUsageStatus = Field(
        nullable=False, default=ResourceUsageStatus.SUBMITTED
    )
    preferred_sites: str | None = Field(nullable=True)
    preferred_locations: str | None = Field(nullable=True)
    preferred_identity_providers: str | None = Field(nullable=True)
    preferred_start_date: date | None = Field(nullable=True)
    preferred_end_date: date | None = Field(nullable=True)
    issuer_id: int = Field(foreign_key="user_group_managers.id", nullable=False)
    moderator_id: int | None = Field(foreign_key="sla_moderators.id", nullable=True)

    issuer: "UserGroupManager" = Relationship(back_populates="submitted_requests")
    moderator: Optional["SLAModerator"] = Relationship(
        back_populates="assigned_requests"
    )
    negotiations: list["SLANegotiation"] = Relationship(back_populates="parent_request")
    tot_block_storage_quota: Optional["TotBlockStorageQuota"] = Relationship(
        back_populates="mentioning_request", sa_relationship_kwargs={"uselist": False}
    )
    tot_compute_quota: Optional["TotComputeQuota"] = Relationship(
        back_populates="mentioning_request", sa_relationship_kwargs={"uselist": False}
    )
    tot_network_quota: Optional["TotNetworkQuota"] = Relationship(
        back_populates="mentioning_request", sa_relationship_kwargs={"uselist": False}
    )
    user_block_storage_quota: Optional["UserBlockStorageQuota"] = Relationship(
        back_populates="mentioning_request", sa_relationship_kwargs={"uselist": False}
    )
    user_compute_quota: Optional["UserComputeQuota"] = Relationship(
        back_populates="mentioning_request", sa_relationship_kwargs={"uselist": False}
    )
    user_network_quota: Optional["UserNetworkQuota"] = Relationship(
        back_populates="mentioning_request", sa_relationship_kwargs={"uselist": False}
    )


class SLANegotiation(RequestBase, table=True):
    __tablename__ = "sla_negotiations"

    status: SLANegotiationStatus = Field(
        nullable=False, default=SLANegotiationStatus.SUBMITTED
    )
    provider_id: int = Field(foreign_key=PROV_ID_COL, nullable=False)
    parent_request_id: int = Field(foreign_key="resource_usages.id", nullable=False)

    provider: "Provider" = Relationship(back_populates="negotiations")
    parent_request: "ResourceUsage" = Relationship(back_populates="negotiations")
    sla: Optional["SLA"] = Relationship(back_populates="negotiation")


class Provider(SQLModel, table=True):
    __tablename__ = "providers"

    id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    type: ProviderType = Field(nullable=False)
    auth_url: str = Field(nullable=False)
    is_public: bool = Field(default=False)
    status: ProviderStatus = Field(nullable=False, default=ProviderStatus.ACTIVE)
    # vol_types: str = Field(nullable=False)
    description: str | None = Field(nullable=True)
    image_tags: str | None = Field(nullable=True)
    network_tags: str | None = Field(nullable=True)
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
    description: str | None = Field(nullable=True)
    provider_id: int = Field(foreign_key=PROV_ID_COL, nullable=False)
    location_id: int | None = Field(foreign_key="locations.id", nullable=True)

    provider: "Provider" = Relationship(back_populates="regions")
    location: Optional["Location"] = Relationship(back_populates="regions")


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: int = Field(primary_key=True)
    site: str = Field(nullable=False)
    country: str = Field(nullable=False)
    description: str | None = Field(nullable=True)
    latitude: float | None = Field(nullable=True, ge=-90.0, le=90.0)
    longitude: float | None = Field(nullable=True, ge=-180.0, le=180.0)

    regions: list["Region"] = Relationship(back_populates="location")


class IdentityProvider(SQLModel, table=True):
    __tablename__ = "identity_providers"

    id: int = Field(primary_key=True)
    endpoint: str = Field(nullable=False)
    description: str | None = Field(nullable=True)

    authorized_providers: list["Trusts"] = Relationship(
        back_populates="identity_providers"
    )


class Quota(SQLModel):
    id: int | None = Field(primary_key=True)
    mentioning_request_id: int = Field(foreign_key="resource_usages.id", nullable=False)
    sla_id: int | None = Field(foreign_key="slas.id", nullable=True)


class BlockStorageQuota(Quota):
    gigabytes: int | None = Field(nullable=True)
    per_volume_gigabytes: int | None = Field(nullable=True)
    volumes: int | None = Field(nullable=True)


class TotBlockStorageQuota(BlockStorageQuota, table=True):
    __tablename__ = "tot_block_storage_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="tot_block_storage_quota"
    )
    sla: Optional["SLA"] = Relationship(back_populates="tot_block_storage_quota")


class UserBlockStorageQuota(BlockStorageQuota, table=True):
    __tablename__ = "user_block_storage_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="user_block_storage_quota"
    )
    sla: Optional["SLA"] = Relationship(back_populates="user_block_storage_quota")


class ComputeQuota(Quota):
    cores: int | None = Field(nullable=True)
    instances: int | None = Field(nullable=True)
    ram: int | None = Field(nullable=True)


class TotComputeQuota(ComputeQuota, table=True):
    __tablename__ = "tot_compute_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="tot_compute_quota"
    )
    sla: Optional["SLA"] = Relationship(back_populates="tot_compute_quota")


class UserComputeQuota(ComputeQuota, table=True):
    __tablename__ = "user_compute_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="user_compute_quota"
    )
    sla: Optional["SLA"] = Relationship(back_populates="user_compute_quota")


class NetworkQuota(Quota):
    networks: int | None = Field(nullable=True)
    ports: int | None = Field(nullable=True)
    public_ips: int | None = Field(nullable=True)
    security_groups: int | None = Field(nullable=True)
    security_group_rules: int | None = Field(nullable=True)


class TotNetworkQuota(NetworkQuota, table=True):
    __tablename__ = "tot_network_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="tot_network_quota"
    )
    sla: Optional["SLA"] = Relationship(back_populates="tot_network_quota")


class UserNetworkQuota(NetworkQuota, table=True):
    __tablename__ = "user_network_quotas"

    mentioning_request: "ResourceUsage" = Relationship(
        back_populates="user_network_quota"
    )
    sla: Optional["SLA"] = Relationship(back_populates="user_network_quota")


class SLA(SQLModel, table=True):
    __tablename__ = "slas"

    id: int | None = Field(primary_key=True)
    doc_uuid: str | None = Field(nullable=True)
    start_date: date = Field(nullable=False)
    end_date: date = Field(nullable=False)
    status: SLAStatus = Field(nullable=False, default=SLAStatus.DISCUSSING)
    negotiation_id: int | None = Field(
        foreign_key="sla_negotiations.id", nullable=False
    )

    negotiation: "SLANegotiation" = Relationship(
        back_populates="sla", sa_relationship_kwargs={"uselist": False}
    )
    tot_block_storage_quota: Optional["TotBlockStorageQuota"] = Relationship(
        back_populates="sla", sa_relationship_kwargs={"uselist": False}
    )
    tot_compute_quota: Optional["TotComputeQuota"] = Relationship(
        back_populates="sla", sa_relationship_kwargs={"uselist": False}
    )
    tot_network_quota: Optional["TotNetworkQuota"] = Relationship(
        back_populates="sla", sa_relationship_kwargs={"uselist": False}
    )
    user_block_storage_quota: Optional["UserBlockStorageQuota"] = Relationship(
        back_populates="sla", sa_relationship_kwargs={"uselist": False}
    )
    user_compute_quota: Optional["UserComputeQuota"] = Relationship(
        back_populates="sla", sa_relationship_kwargs={"uselist": False}
    )
    user_network_quota: Optional["UserNetworkQuota"] = Relationship(
        back_populates="sla", sa_relationship_kwargs={"uselist": False}
    )


class Query(SQLModel):
    """Model to filter lists in GET operations with multiple items.

    Attributes:
    ----------
        size (int): Chunk size.
        offset (int): Divide the list in chunks.
        sort (str | None): sorting criteria.
    """

    size: int = Field(default=100, ge=1, le=100, description="Chunk size.")
    offset: int = Field(default=0, ge=0, description="Divide the list in chunks")
    sort: str | None = Field(default=None, description="Sorting criteria")

    @validator("offset", pre=True)
    @classmethod
    def set_offset_to_0(cls, v: int, values: dict[str, Any]) -> int:
        """If chunk size is 0 set page index to 0."""
        if values.get("offset") is None:
            return 0
        return v

    @validator("sort")
    @classmethod
    def parse_sort_rule(cls, v: str | None) -> str | None:
        """Parse and correct sort rule.

        Remove `_asc` or `_desc` suffix. Prepend `-` when `_desc` is received.
        """
        if v is None:
            return v

        if v.endswith("_asc"):
            return v[: -len("_asc")]
        elif v.endswith("_desc"):
            if v.startswith("-"):
                return v[: -len("_desc")]
            return f"-{v[: -len('_desc')]}"
        return v


# WORKFLOWS


class WorkflowSpec(SQLModel, table=True):
    """DB model representing a Workflow (Process) specification."""

    __tablename__ = "workflow_specs"

    id: int = Field(primary_key=True, index=True)
    description: str = Field(nullable=False)
    file: str = Field(nullable=False)
    name: str = Field(nullable=False)
    typename: str = Field(nullable=False)
    io_specification: str = Field(nullable=True)
    data_objects: str = Field(nullable=True)
    correlation_keys: str = Field(nullable=True)

    task_specs: list["TaskSpec"] = Relationship(
        back_populates="workflow_spec",
        sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
    )
    children: list["WorkflowSpec"] = Relationship(
        sa_relationship_kwargs={
            "secondary": "workflow_spec_dependencies",
            "primaryjoin": "WorkflowSpec.id == WorkflowSpecDependency.parent_id",
            "secondaryjoin": "WorkflowSpec.id == WorkflowSpecDependency.child_id",
            "cascade": "all,delete",
        },
        back_populates="parents",
    )
    parents: list["WorkflowSpec"] = Relationship(
        sa_relationship_kwargs={
            "secondary": "workflow_spec_dependencies",
            "primaryjoin": "WorkflowSpec.id == WorkflowSpecDependency.child_id",
            "secondaryjoin": "WorkflowSpec.id == WorkflowSpecDependency.parent_id",
        },
        back_populates="children",
    )
    workflows: list["Workflow"] = Relationship(back_populates="workflow_spec")


class WorkflowSpecDependency(SQLModel, table=True):
    __tablename__ = "workflow_spec_dependencies"

    parent_id: int = Field(
        foreign_key="workflow_specs.id", primary_key=True, index=True
    )
    child_id: int = Field(foreign_key="workflow_specs.id", primary_key=True, index=True)


class TaskSpec(SQLModel, table=True):
    """DB model representing a generic Task specification."""

    __tablename__ = "task_specs"

    name: str = Field(primary_key=True, index=True)
    description: str = Field(nullable=False)
    manual: bool = Field(nullable=False)
    lookahead: int = Field(nullable=False)
    typename: str = Field(nullable=False)
    event_definition: str | None = Field(nullable=True)
    cancel_activity: bool | None = Field(nullable=True)
    default_task_spec: str | None = Field(nullable=True)
    cond_task_specs: str | None = Field(nullable=True)
    workflow_spec_id: int = Field(foreign_key="workflow_specs.id", nullable=False)

    workflow_spec: "WorkflowSpec" = Relationship(back_populates="task_specs")
    inputs: list["TaskSpec"] = Relationship(
        sa_relationship_kwargs={
            "secondary": "task_spec_associations",
            "primaryjoin": "TaskSpec.name == TaskSpecAssociation.output_name",
            "secondaryjoin": "TaskSpec.name == TaskSpecAssociation.input_name",
        },
        back_populates="outputs",
    )
    outputs: list["TaskSpec"] = Relationship(
        sa_relationship_kwargs={
            "secondary": "task_spec_associations",
            "primaryjoin": "TaskSpec.name == TaskSpecAssociation.input_name",
            "secondaryjoin": "TaskSpec.name == TaskSpecAssociation.output_name",
        },
        back_populates="inputs",
    )
    tasks: list["Task"] = Relationship(back_populates="task_spec")


class TaskSpecAssociation(SQLModel, table=True):
    """Association table to determine Tasks specification hierarchy."""

    __tablename__ = "task_spec_associations"
    input_name: str = Field(foreign_key="task_specs.name", primary_key=True)
    output_name: str = Field(foreign_key="task_specs.name", primary_key=True)


def set_ended_time(context):
    return func.now() if context.get_current_parameters()["active_tasks"] == 0 else None


class Workflow(SQLModel, table=True):
    """DB model representing a Workflow instance."""

    __tablename__ = "workflows"

    id: int | None = Field(primary_key=True)
    typename: str = Field(nullable=False)
    root: str = Field(nullable=False)
    last_task: str = Field(nullable=True)
    success: bool = Field(nullable=False)
    subprocesses: str = Field(nullable=True)
    # bullshit: str = Field()
    active_tasks: int = Field(default=0, nullable=False)
    started: datetime = Field(default=func.now(), nullable=False)
    updated: datetime = Field(nullable=True, sa_column_kwargs={"onupdate": func.now()})
    ended: datetime = Field(
        nullable=True, sa_column_kwargs={"onupdate": set_ended_time}
    )
    workflow_spec_id: int = Field(foreign_key="workflow_specs.id", nullable=False)

    workflow_spec: "WorkflowSpec" = Relationship(back_populates="workflows")
    workflow_data: list["WorkflowData"] = Relationship(
        back_populates="workflow",
        sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
    )
    tasks: list["Task"] = Relationship(
        back_populates="workflow",
        sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
    )


class WorkflowData(SQLModel, table=True):
    """DB model representing a subset of the data belonging to a Workflow instance."""

    __tablename__ = "workflow_data"

    name: str = Field(primary_key=True, index=True)
    value: str = Field()
    last_updated: datetime = Field(default=func.now())
    workflow_id: int = Field(foreign_key="workflows.id", primary_key=True, index=True)

    workflow: "Workflow" = Relationship(back_populates="workflow_data")


class Task(SQLModel, table=True):
    """DB model representing a Task instance."""

    __tablename__ = "tasks"

    id: str | None = Field(primary_key=True, index=True)
    state: int = Field(nullable=False)
    typename: str = Field(nullable=False)
    last_state_change: int = Field(nullable=False)
    triggered: bool = Field(nullable=False)
    workflow_id: int = Field(foreign_key="workflows.id", nullable=False, index=True)
    task_spec_name: str = Field(foreign_key="task_specs.name", nullable=False)

    workflow: "Workflow" = Relationship(back_populates="tasks")
    task_spec: "TaskSpec" = Relationship(back_populates="tasks")
    task_data: list["TaskData"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"cascade": "all,delete,delete-orphan"},
    )
    parent: "Task" = Relationship(
        sa_relationship_kwargs={
            "secondary": "task_associations",
            "primaryjoin": "Task.id == TaskAssociation.child_id",
            "secondaryjoin": "Task.id == TaskAssociation.parent_id",
        },
        back_populates="children",
    )
    children: list["Task"] = Relationship(
        sa_relationship_kwargs={
            "secondary": "task_associations",
            "primaryjoin": "Task.id == TaskAssociation.parent_id",
            "secondaryjoin": "Task.id == TaskAssociation.child_id",
        },
        back_populates="parent",
    )


class TaskAssociation(SQLModel, table=True):
    """Association table to determine Tasks hierarchy."""

    __tablename__ = "task_associations"
    parent_id: str = Field(foreign_key="tasks.id", primary_key=True)
    child_id: str = Field(foreign_key="tasks.id", primary_key=True)


class TaskData(SQLModel, table=True):
    """DB model representing a subset of the data belonging to a Task instance."""

    __tablename__ = "task_data"

    name: str = Field(primary_key=True, index=True)
    value: str = Field()
    last_updated: datetime = Field(default=func.now())
    task_id: int = Field(foreign_key="tasks.id", primary_key=True, index=True)

    task: "Task" = Relationship(back_populates="task_data")
