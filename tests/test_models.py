from datetime import datetime
from typing import Any, Type

import pytest
from pytest_cases import parametrize, parametrize_with_cases
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from enums import ResourceUsageStatus, SLANegotiationStatus
from models import (
    Admin,
    Provider,
    ResourceUsage,
    SLANegotiation,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    TotBlockStorageQuota,
    TotComputeQuota,
    TotNetworkQuota,
    User,
    UserBlockStorageQuota,
    UserComputeQuota,
    UserGroupManager,
    UserNetworkQuota,
)
from tests.item_data import (
    block_storage_dict,
    compute_dict,
    network_dict,
    provider_dict,
    request_dict,
    user_dict,
)
from tests.utils import random_lower_string, random_start_end_dates


class CaseUserDerived:
    @parametrize(cls=[Admin, SiteAdmin, SiteTester, SLAModerator, UserGroupManager])
    def case_user(self, cls) -> Any:
        return cls


class CaseResourceUsageData:
    def case_short(self) -> dict[str, datetime]:
        return request_dict()

    def case_message(self) -> dict[str, Any]:
        return {**request_dict(), "message": random_lower_string()}

    def case_start_end_date(self) -> dict[str, Any]:
        start_date, end_date = random_start_end_dates()
        return {
            **request_dict(),
            "preferred_start_date": start_date,
            "preferred_end_date": end_date,
        }

    def case_sites(self) -> dict[str, Any]:
        return {**request_dict(), "preferred_sites": random_lower_string()}

    def case_locations(self) -> dict[str, Any]:
        return {**request_dict(), "preferred_locations": random_lower_string()}

    def case_identity_providers(self) -> dict[str, Any]:
        return {**request_dict(), "preferred_identity_providers": random_lower_string()}


class CaseQuotaDerived:
    @parametrize(cls=[TotBlockStorageQuota, UserBlockStorageQuota])
    def case_block_storage(self, cls) -> tuple[Any, dict[str, int]]:
        return cls, block_storage_dict()

    @parametrize(cls=[TotComputeQuota, UserComputeQuota])
    def case_compute(self, cls) -> tuple[Any, dict[str, int]]:
        return cls, compute_dict()

    @parametrize(cls=[TotNetworkQuota, UserNetworkQuota])
    def case_network(self, cls) -> tuple[Any, dict[str, int]]:
        return cls, network_dict()


class CaseQuotaScope:
    @parametrize(q_scope=["tot", "per_user"])
    def case_quota_type(self, q_scope: str) -> str:
        return q_scope


def test_user(db_session: Session) -> None:
    d = user_dict()
    item = User(**d)
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    assert item.id is not None
    assert item.name == d["name"]
    assert item.email == d["email"]


@parametrize_with_cases("cls", cases=CaseUserDerived)
def test_user_derived_cls(db_session: Any, db_user: User, cls: Type[Any]) -> None:
    item = cls(id=db_user.id)
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    assert db_user.id is not None
    assert item.id is not None
    assert item.id == db_user.id


@parametrize_with_cases("data", cases=CaseResourceUsageData)
def test_resource_usage_request(
    db_session: Session, db_user_group_manager: UserGroupManager, data: dict[str, Any]
) -> None:
    assert len(db_user_group_manager.submitted_requests) == 0

    resource_usage_request = ResourceUsage(**data, issuer=db_user_group_manager)
    db_session.add(resource_usage_request)
    db_session.commit()
    db_session.refresh(resource_usage_request)

    assert db_user_group_manager.id is not None
    assert len(db_user_group_manager.submitted_requests) == 1
    assert resource_usage_request.id == db_user_group_manager.submitted_requests[0].id
    assert resource_usage_request.issuer_id == db_user_group_manager.id

    assert resource_usage_request.id is not None
    assert resource_usage_request.status == ResourceUsageStatus.SUBMITTED
    assert resource_usage_request.issue_date == data.get("issue_date")
    assert resource_usage_request.update_date == data.get("update_date")
    assert resource_usage_request.message == data.get("message")
    assert resource_usage_request.preferred_start_date == data.get(
        "preferred_start_date"
    )
    assert resource_usage_request.preferred_end_date == data.get("preferred_end_date")
    assert resource_usage_request.preferred_sites == data.get("preferred_sites")
    assert resource_usage_request.preferred_locations == data.get("preferred_locations")
    assert resource_usage_request.preferred_identity_providers == data.get(
        "preferred_identity_providers"
    )

    assert resource_usage_request.moderator_id is None
    assert resource_usage_request.moderator is None


def test_resource_usage_request_without_issuer(db_session: Session) -> None:
    data = request_dict()
    item = ResourceUsage(**data)
    db_session.add(item)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_assigned_moderator_to_resource_usage_request(
    db_session: Session,
    db_sla_moderator: SLAModerator,
    db_resource_usage_request: ResourceUsage,
) -> None:
    assert len(db_sla_moderator.assigned_requests) == 0

    db_sla_moderator.assigned_requests.append(db_resource_usage_request)
    db_session.add(db_sla_moderator)
    db_session.commit()
    db_session.refresh(db_sla_moderator)

    assert len(db_sla_moderator.assigned_requests) == 1
    assert db_sla_moderator.assigned_requests[0].id == db_resource_usage_request.id
    assert db_sla_moderator.id == db_resource_usage_request.moderator.id
    assert db_sla_moderator.id == db_resource_usage_request.moderator_id


@parametrize_with_cases("quota_scope", cases=CaseQuotaScope)
def test_block_storage_quota(
    db_session: Session, db_resource_usage_request: ResourceUsage, quota_scope: str
) -> None:
    data = block_storage_dict()
    if quota_scope == "tot":
        assert db_resource_usage_request.tot_block_storage_quota is None
        quota = TotBlockStorageQuota(
            **data, mentioning_request=db_resource_usage_request
        )
    elif quota_scope == "per_user":
        assert db_resource_usage_request.user_block_storage_quota is None
        quota = UserBlockStorageQuota(
            **data, mentioning_request=db_resource_usage_request
        )

    db_session.add(quota)
    db_session.commit()
    db_session.refresh(quota)

    assert quota.id is not None
    assert quota.gigabytes == data.get("gigabytes")
    assert quota.per_volume_gigabytes == data.get("per_volume_gigabytes")
    assert quota.volumes == data.get("volumes")
    assert quota.mentioning_request_id == db_resource_usage_request.id
    if quota_scope == "tot":
        assert quota.id == db_resource_usage_request.tot_block_storage_quota.id
    elif quota_scope == "per_user":
        assert quota.id == db_resource_usage_request.user_block_storage_quota.id


@parametrize_with_cases("quota_scope", cases=CaseQuotaScope)
def test_compute_quota(
    db_session: Session, db_resource_usage_request: ResourceUsage, quota_scope: str
) -> None:
    data = compute_dict()
    if quota_scope == "tot":
        assert db_resource_usage_request.tot_compute_quota is None
        quota = TotComputeQuota(**data, mentioning_request=db_resource_usage_request)
    elif quota_scope == "per_user":
        assert db_resource_usage_request.user_compute_quota is None
        quota = UserComputeQuota(**data, mentioning_request=db_resource_usage_request)

    db_session.add(quota)
    db_session.commit()
    db_session.refresh(quota)

    assert quota.id is not None
    assert quota.cores == data.get("cores")
    assert quota.instances == data.get("instances")
    assert quota.ram == data.get("ram")
    assert quota.mentioning_request_id == db_resource_usage_request.id
    if quota_scope == "tot":
        assert quota.id == db_resource_usage_request.tot_compute_quota.id
    elif quota_scope == "per_user":
        assert quota.id == db_resource_usage_request.user_compute_quota.id


@parametrize_with_cases("quota_scope", cases=CaseQuotaScope)
def test_network_quota(
    db_session: Session, db_resource_usage_request: ResourceUsage, quota_scope: str
) -> None:
    data = network_dict()
    if quota_scope == "tot":
        assert db_resource_usage_request.tot_network_quota is None
        quota = TotNetworkQuota(**data, mentioning_request=db_resource_usage_request)
    elif quota_scope == "per_user":
        assert db_resource_usage_request.user_network_quota is None
        quota = UserNetworkQuota(**data, mentioning_request=db_resource_usage_request)

    db_session.add(quota)
    db_session.commit()
    db_session.refresh(quota)

    assert quota.id is not None
    assert quota.networks == data.get("networks")
    assert quota.ports == data.get("ports")
    assert quota.public_ips == data.get("public_ips")
    assert quota.security_groups == data.get("security_groups")
    assert quota.security_group_rules == data.get("security_group_rules")
    assert quota.mentioning_request_id == db_resource_usage_request.id
    if quota_scope == "tot":
        assert quota.id == db_resource_usage_request.tot_network_quota.id
    elif quota_scope == "per_user":
        assert quota.id == db_resource_usage_request.user_network_quota.id


@parametrize_with_cases("cls, data", cases=CaseQuotaDerived)
def test_quota_without_res_usage_req(
    db_session: Session, cls: Any, data: dict[str, int]
) -> None:
    quota = cls(**data)
    db_session.add(quota)
    with pytest.raises(IntegrityError):
        db_session.commit()


@parametrize_with_cases("cls, data", cases=CaseQuotaDerived)
def test_quota_wit_multi_res_usage_req(
    db_session: Session,
    db_resource_usage_request: ResourceUsage,
    cls: Any,
    data: dict[str, int],
) -> None:
    quota = cls(
        **data,
        mentioning_requests=[db_resource_usage_request, db_resource_usage_request],
    )
    db_session.add(quota)
    with pytest.raises(IntegrityError):
        db_session.commit()


# TODO: Test provider

# def test_provider(db_session: Session) -> None:
#     data = provider_dict()
#     provider = Provider(**data)
#     db_session.add(provider)
#     db_session.commit()
#     db_session.refresh(provider)

#     assert provider.id is not None
#     assert provider.name == data.get("name")
#     assert provider.description == data.get("description")
#     assert provider.url == data.get("url")
#     assert provider.email == data.get("email")
#     assert provider.logo == data.get("logo")
#     assert provider.logo_url == data.get("logo_url")


def test_sla_negotiation(
    db_session: Session,
    db_provider: Provider,
    db_resource_usage_request: ResourceUsage,
) -> None:
    assert len(db_resource_usage_request.negotiations) == 0
    assert len(db_provider.negotiations) == 0

    data = request_dict()
    negotiation = SLANegotiation(
        **data, parent_request=db_resource_usage_request, provider=db_provider
    )
    db_session.add(negotiation)
    db_session.commit()
    db_session.refresh(negotiation)

    assert db_resource_usage_request.id is not None
    assert len(db_resource_usage_request.negotiations) == 1
    assert negotiation.id == db_resource_usage_request.negotiations[0].id
    assert negotiation.parent_request_id == db_resource_usage_request.id

    assert db_provider.id is not None
    assert len(db_provider.negotiations) == 1
    assert negotiation.id == db_provider.negotiations[0].id
    assert negotiation.provider_id == db_provider.id

    assert negotiation.id is not None
    assert negotiation.status == SLANegotiationStatus.SUBMITTED
    assert negotiation.issue_date == data.get("issue_date")
    assert negotiation.update_date == data.get("update_date")
    assert negotiation.message == data.get("message")

    assert negotiation.sla_id is None
    assert negotiation.sla is None


# TODO test SLA (with and without quotas)
# TODO test negotiation with SLA


def test_negotiation_without_provider(
    db_session: Session, db_resource_usage_request: ResourceUsage
) -> None:
    data = request_dict()
    item = SLANegotiation(**data, parent_request=db_resource_usage_request)
    db_session.add(item)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_negotiation_without_parent_request(
    db_session: Session, db_provider: Provider
) -> None:
    data = request_dict()
    item = SLANegotiation(**data, provider=db_provider)
    db_session.add(item)
    with pytest.raises(IntegrityError):
        db_session.commit()
