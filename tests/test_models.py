from datetime import datetime
from random import getrandbits
from typing import Any, Type

import pytest
from fed_reg.provider.enum import ProviderStatus
from pydantic import AnyHttpUrl
from pytest_cases import case, get_case_tags, parametrize, parametrize_with_cases
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from fed_mng.enums import ResourceUsageStatus, SLANegotiationStatus, SLAStatus
from fed_mng.models import (
    SLA,
    Admin,
    IdentityProvider,
    Location,
    Provider,
    Region,
    ResourceUsage,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    SLANegotiation,
    TotBlockStorageQuota,
    TotComputeQuota,
    TotNetworkQuota,
    Trusts,
    User,
    UserBlockStorageQuota,
    UserComputeQuota,
    UserGroupManager,
    UserNetworkQuota,
)
from tests.item_data import (
    block_storage_dict,
    compute_dict,
    identity_provider_dict,
    location_dict,
    network_dict,
    provider_dict,
    region_dict,
    request_dict,
    sla_dict,
    user_dict,
)
from tests.utils import (
    random_float,
    random_lower_string,
    random_provider_status,
    random_sla_status,
    random_start_end_dates,
)


class CaseUserDerived:
    @parametrize(cls=[Admin, SiteAdmin, SiteTester, SLAModerator, UserGroupManager])
    def case_user(self, cls) -> Any:
        return cls


class CaseSLAData:
    def case_short(self) -> dict[str, datetime]:
        return sla_dict()

    def case_doc_uuid(self) -> dict[str, Any]:
        return {**sla_dict(), "doc_uuid": random_lower_string()}

    def case_status(self) -> dict[str, Any]:
        return {**sla_dict(), "status": random_sla_status()}


class CaseIdentityProviderData:
    def case_short(self) -> dict[str, AnyHttpUrl]:
        return identity_provider_dict()

    def case_desc(self) -> dict[str, Any]:
        return {**identity_provider_dict(), "description": random_lower_string()}


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


class CaseProviderData:
    def case_short(self) -> dict[str, datetime]:
        return provider_dict()

    def case_desc(self) -> dict[str, Any]:
        return {**provider_dict(), "description": random_lower_string()}

    def case_image_tags(self) -> dict[str, Any]:
        return {**provider_dict(), "image_tags": random_lower_string()}

    def case_network_tags(self) -> dict[str, Any]:
        return {**provider_dict(), "network_tags": random_lower_string()}

    def case_status(self) -> dict[str, Any]:
        return {**provider_dict(), "status": random_provider_status()}

    def case_is_public(self) -> dict[str, Any]:
        return {**provider_dict(), "is_public": getrandbits(1)}


class CaseRegionData:
    def case_short(self) -> dict[str, str]:
        return region_dict()

    def case_desc(self) -> dict[str, str]:
        return {**region_dict(), "description": random_lower_string()}


class CaseLocationData:
    def case_short(self) -> dict[str, str]:
        return location_dict()

    def case_desc(self) -> dict[str, str]:
        return {**location_dict(), "description": random_lower_string()}

    def case_latitude(self) -> dict[str, str]:
        return {**location_dict(), "latitude": random_float(-90, 90)}

    def case_longitude(self) -> dict[str, str]:
        return {**location_dict(), "longitude": random_float(-180, 180)}


class CaseInvalidLocationData:
    @parametrize(value=[-91, 91])
    def case_latitude(self, value: float) -> dict[str, Any]:
        return {"latitude": value}

    @parametrize(value=[-181, 181])
    def case_longitude(self, value: float) -> dict[str, Any]:
        return {"longitude": value}


class CaseQuotaDerived:
    @case(tags=["tot", "block_storage"])
    def case_tot_block_storage(self) -> TotBlockStorageQuota:
        return TotBlockStorageQuota(**block_storage_dict())

    @case(tags=["user", "block_storage"])
    def case_user_block_storage(self) -> UserBlockStorageQuota:
        return UserBlockStorageQuota(**block_storage_dict())

    @case(tags=["tot", "compute"])
    def case_tot_compute(self) -> TotComputeQuota:
        return TotComputeQuota(**compute_dict())

    @case(tags=["user", "compute"])
    def case_user_compute(self) -> UserComputeQuota:
        return UserComputeQuota(**compute_dict())

    @case(tags=["tot", "network"])
    def case_tot_network(self) -> TotNetworkQuota:
        return TotNetworkQuota(**network_dict())

    @case(tags=["user", "network"])
    def case_user_network(self) -> UserNetworkQuota:
        return UserNetworkQuota(**network_dict())


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

    assert resource_usage_request.tot_block_storage_quota is None
    assert resource_usage_request.tot_compute_quota is None
    assert resource_usage_request.tot_network_quota is None
    assert resource_usage_request.user_block_storage_quota is None
    assert resource_usage_request.user_compute_quota is None
    assert resource_usage_request.user_network_quota is None


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


@parametrize_with_cases("quota", cases=CaseQuotaDerived)
def test_quota_without_res_usage_req(db_session: Session, quota: Any) -> None:
    db_session.add(quota)
    with pytest.raises(IntegrityError):
        db_session.commit()


@parametrize_with_cases("quota", cases=CaseQuotaDerived)
def test_quota_wit_multi_res_usage_req(
    db_resource_usage_request: ResourceUsage, quota: Any
) -> None:
    with pytest.raises(AttributeError):
        quota.mentioning_request = [
            db_resource_usage_request,
            db_resource_usage_request,
        ]


@parametrize_with_cases("data", cases=CaseProviderData)
def test_provider(db_session: Session, data: dict[str, Any]) -> None:
    provider = Provider(**data)
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    assert provider.id is not None
    assert provider.name == data.get("name")
    assert provider.type == data.get("type")
    assert provider.auth_url == data.get("auth_url")
    assert provider.is_public == data.get("is_public", False)
    assert provider.status == data.get("status", ProviderStatus.ACTIVE)
    assert provider.description == data.get("description")
    assert provider.image_tags == data.get("image_tags")
    assert provider.network_tags == data.get("network_tags")

    assert len(provider.regions) == 0
    assert len(provider.site_admins) == 0
    assert len(provider.trusted_identity_providers) == 0
    assert len(provider.negotiations) == 0


def test_provider_with_site_admins(
    db_session: Session, db_provider: Provider, db_site_admin: SiteAdmin
) -> None:
    assert len(db_provider.site_admins) == 0

    db_provider.site_admins.append(db_site_admin)
    db_session.add(db_provider)
    db_session.commit()
    db_session.refresh(db_provider)

    assert len(db_provider.site_admins) == 1
    assert db_provider.site_admins[0].id == db_site_admin.id
    assert len(db_site_admin.providers) == 1
    assert db_provider.id == db_site_admin.providers[0].id


# TODO: Test Provider federation requests
# TODO: Test provider with versions and mentioning request


@parametrize_with_cases("data", cases=CaseIdentityProviderData)
def test_identity_provider(db_session: Session, data: dict[str, Any]) -> None:
    identity_provider = IdentityProvider(**data)

    db_session.add(identity_provider)
    db_session.commit()
    db_session.refresh(identity_provider)

    assert identity_provider.id is not None
    assert identity_provider.endpoint == data.get("endpoint")
    assert identity_provider.description == data.get("description")
    assert len(identity_provider.authorized_providers) == 0


def test_identity_provider_with_provider(
    db_session: Session, db_identity_provider: IdentityProvider, db_provider: Provider
) -> None:
    assert len(db_identity_provider.authorized_providers) == 0
    assert len(db_provider.trusted_identity_providers) == 0

    # Create the trust association object and link it
    trust = Trusts(idp_name=random_lower_string(), protocol=random_lower_string())
    trust.provider = db_provider
    db_identity_provider.authorized_providers.append(trust)

    db_session.add(db_identity_provider)
    db_session.commit()
    db_session.refresh(db_identity_provider)

    assert len(db_identity_provider.authorized_providers) == 1
    assert db_identity_provider.authorized_providers[0].provider_id == db_provider.id
    assert (
        db_identity_provider.authorized_providers[0].identity_provider_id
        == db_identity_provider.id
    )
    assert len(db_provider.trusted_identity_providers) == 1
    assert db_provider.trusted_identity_providers[0].provider_id == db_provider.id
    assert (
        db_provider.trusted_identity_providers[0].identity_provider_id
        == db_identity_provider.id
    )


def test_identity_provider_with_multi_providers(
    db_session: Session, db_identity_provider: IdentityProvider, db_provider: Provider
) -> None:
    assert len(db_identity_provider.authorized_providers) == 0
    assert len(db_provider.trusted_identity_providers) == 0

    # Create the trust association object and link it
    trust = Trusts(idp_name=random_lower_string(), protocol=random_lower_string())
    trust.provider = db_provider
    db_identity_provider.authorized_providers.append(trust)

    db_provider2 = Provider(**provider_dict())
    trust = Trusts(idp_name=random_lower_string(), protocol=random_lower_string())
    trust.provider = db_provider2
    db_identity_provider.authorized_providers.append(trust)

    db_session.add(db_identity_provider)
    db_session.commit()
    db_session.refresh(db_identity_provider)

    assert len(db_identity_provider.authorized_providers) == 2
    assert db_identity_provider.authorized_providers[0].provider_id == db_provider.id
    assert db_identity_provider.authorized_providers[1].provider_id == db_provider2.id
    assert (
        db_identity_provider.authorized_providers[0].identity_provider_id
        == db_identity_provider.id
    )
    assert (
        db_identity_provider.authorized_providers[1].identity_provider_id
        == db_identity_provider.id
    )

    assert len(db_provider.trusted_identity_providers) == 1
    assert db_provider.trusted_identity_providers[0].provider_id == db_provider.id
    assert (
        db_provider.trusted_identity_providers[0].identity_provider_id
        == db_identity_provider.id
    )
    assert db_provider2.trusted_identity_providers[0].provider_id == db_provider2.id
    assert (
        db_provider2.trusted_identity_providers[0].identity_provider_id
        == db_identity_provider.id
    )


def test_provider_with_multi_identity_providers(
    db_session: Session, db_identity_provider: IdentityProvider, db_provider: Provider
) -> None:
    assert len(db_identity_provider.authorized_providers) == 0
    assert len(db_provider.trusted_identity_providers) == 0

    # Create the trust association object and link it
    trust = Trusts(idp_name=random_lower_string(), protocol=random_lower_string())
    trust.provider = db_provider
    db_identity_provider.authorized_providers.append(trust)

    db_identity_provider2 = IdentityProvider(**identity_provider_dict())
    trust = Trusts(idp_name=random_lower_string(), protocol=random_lower_string())
    trust.provider = db_provider
    db_identity_provider2.authorized_providers.append(trust)

    db_session.add(db_provider)
    db_session.commit()
    db_session.refresh(db_provider)

    assert len(db_identity_provider.authorized_providers) == 1
    assert db_identity_provider.authorized_providers[0].provider_id == db_provider.id
    assert (
        db_identity_provider.authorized_providers[0].identity_provider_id
        == db_identity_provider.id
    )
    assert len(db_identity_provider2.authorized_providers) == 1
    assert db_identity_provider2.authorized_providers[0].provider_id == db_provider.id
    assert (
        db_identity_provider2.authorized_providers[0].identity_provider_id
        == db_identity_provider2.id
    )

    assert len(db_provider.trusted_identity_providers) == 2
    assert db_provider.trusted_identity_providers[0].provider_id == db_provider.id
    assert db_provider.trusted_identity_providers[1].provider_id == db_provider.id
    assert (
        db_provider.trusted_identity_providers[0].identity_provider_id
        == db_identity_provider.id
    )
    assert (
        db_provider.trusted_identity_providers[1].identity_provider_id
        == db_identity_provider2.id
    )


@parametrize_with_cases("data", cases=CaseRegionData)
def test_region(
    db_session: Session, db_provider: Provider, data: dict[str, Any]
) -> None:
    assert len(db_provider.regions) == 0

    region = Region(**data, provider=db_provider)
    db_session.add(region)
    db_session.commit()
    db_session.refresh(region)

    assert len(db_provider.regions) == 1
    assert region.id == db_provider.regions[0].id
    assert region.provider_id == db_provider.id

    assert region.id is not None
    assert region.name == data.get("name")
    assert region.description == data.get("description")

    assert region.location_id is None
    assert region.location is None


def test_region_without_provider(db_session: Session) -> None:
    data = region_dict()
    region = Region(**data)
    db_session.add(region)
    with pytest.raises(IntegrityError):
        db_session.commit()


@parametrize_with_cases("data", cases=CaseLocationData)
def test_location(db_session: Session, data: dict[str, Any]) -> None:
    location = Location(**data)
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)

    assert location.id is not None
    assert location.site == data.get("site")
    assert location.country == data.get("country")
    assert location.description == data.get("description")
    assert location.latitude == data.get("latitude")
    assert location.longitude == data.get("longitude")

    assert len(location.regions) == 0


def test_location_with_region(db_session: Session, db_region: Region) -> None:
    assert db_region.location is None

    data = location_dict()
    location = Location(**data, regions=[db_region])

    # ! Adding multiple times the same region brings the same result
    # location = Location(**data, regions=[db_region, db_region])

    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)

    assert len(location.regions) == 1
    assert location.regions[0].id == db_region.id
    assert location.id == db_region.location_id


def test_location_with_regions(db_session: Session, db_region: Region) -> None:
    assert db_region.location is None

    db_region2 = Region(**region_dict(), provider=db_region.provider)
    location = Location(**location_dict(), regions=[db_region, db_region2])
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)

    assert db_region.location_id is not None
    assert db_region2.location_id is not None
    assert db_region.location_id == db_region2.location_id

    assert len(location.regions) == 2
    assert location.regions[0].id == db_region.id
    assert location.id == db_region.location_id


@parametrize_with_cases("data", cases=CaseInvalidLocationData)
def test_invalid_location(data: dict[str, Any]) -> None:
    """Invalid values are discarded before committing."""
    location = Location(**location_dict(), **data)

    for k, v in data.items():
        assert v is not None
        assert location.__getattribute__(k) is None


def test_negotiation(
    db_session: Session,
    db_provider: Provider,
    db_resource_usage_request: ResourceUsage,
) -> None:
    assert len(db_resource_usage_request.negotiations) == 0
    assert len(db_provider.negotiations) == 0

    data = request_dict()
    negotiation = SLANegotiation(
        **data,
        parent_request=db_resource_usage_request,
        provider=db_provider,
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

    assert negotiation.sla is None


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


@parametrize_with_cases("data", cases=CaseSLAData)
def test_sla(
    db_session: Session, db_negotiation: SLANegotiation, data: dict[str, Any]
) -> None:
    sla = SLA(**data, negotiation=db_negotiation)
    db_session.add(sla)
    db_session.commit()
    db_session.refresh(sla)

    assert sla.id is not None
    assert sla.doc_uuid == data.get("doc_uuid")
    assert sla.start_date == data.get("start_date")
    assert sla.end_date == data.get("end_date")
    assert sla.status == data.get("status", SLAStatus.DISCUSSING)

    assert db_negotiation.id is not None
    assert sla.negotiation_id == db_negotiation.id
    assert sla.negotiation.id == db_negotiation.id
    assert sla.id == db_negotiation.sla.id

    assert sla.tot_block_storage_quota is None
    assert sla.tot_compute_quota is None
    assert sla.tot_network_quota is None
    assert sla.user_block_storage_quota is None
    assert sla.user_compute_quota is None
    assert sla.user_network_quota is None


@parametrize_with_cases("quota", cases=CaseQuotaDerived)
def test_sla_with_quota(
    db_session: Session,
    db_resource_usage_request: ResourceUsage,
    db_sla: SLA,
    quota: Any,
    current_cases: dict,
) -> None:
    tags = get_case_tags(current_cases["quota"].func)
    attr = f"{tags[0]}_{tags[1]}_quota"

    db_sla.__getattribute__(attr)
    quota.mentioning_request = db_resource_usage_request
    db_sla.__setattr__(attr, quota)

    db_session.add(db_sla)
    db_session.commit()
    db_session.refresh(db_sla)

    assert db_sla.__getattribute__(attr) is not None
    assert db_sla.__getattribute__(attr).id == quota.id


def test_sla_without_negotiation(db_session: Session) -> None:
    sla = SLA(**sla_dict())
    db_session.add(sla)
    with pytest.raises(IntegrityError):
        db_session.commit()
