from datetime import datetime
from typing import Any, Type

from pytest_cases import parametrize, parametrize_with_cases
from sqlmodel import Session

from enums import ResourceUsageStatus
from models import (
    Admin,
    ResourceUsage,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    User,
    UserGroupManager,
)
from tests.item_data import request_dict, user_dict
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
