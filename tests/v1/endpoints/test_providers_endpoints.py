"""Integration tests for fed_mgr.v1.providers.endpoints.

Tests in this file:
- test_options_providers
- test_create_provider_success
- test_create_provider_conflict
- test_create_provider_not_null_error
- test_get_providers_success
- test_get_provider_success
- test_get_provider_not_found
- test_edit_provider_success
- test_edit_provider_not_found
- test_edit_provider_conflict
- test_edit_provider_not_null_error
- test_delete_provider_success
- test_update_provider_state_success
- test_update_provider_state_forbidden
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from fed_mgr.config import get_settings
from fed_mgr.exceptions import ConflictError, DeleteFailedError, ItemNotFoundError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.models import Provider
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.schemas import ProviderCreate, ProviderStatus, ProviderUpdate
from fed_mgr.v1.schemas import ItemID


def test_options_providers(client):
    """Test OPTIONS /providers/ returns 204 and Allow header."""
    resp = client.options("/api/v1/providers/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_provider_success(client, session, current_user, provider_data):
    """Test POST /providers/ creates an resource provider and returns 201 with id."""
    fake_id = uuid.uuid4()
    data = {**provider_data, "site_admins": [str(uuid.uuid4())]}
    mock_settings = MagicMock()
    sub_app_v1.dependency_overrides[get_settings] = lambda: mock_settings

    with patch(
        "fed_mgr.v1.providers.endpoints.add_provider", return_value=ItemID(id=fake_id)
    ) as mock_create:
        resp = client.post("/api/v1/providers/", json=data)
        mock_create.assert_called_once_with(
            session=session,
            provider=ProviderCreate(**data),
            created_by=current_user,
            secret_key=mock_settings.SECRET_KEY,
        )
        assert resp.status_code == 201
        assert resp.json() == {"id": str(fake_id)}


def test_create_provider_conflict(client, session, current_user, provider_data):
    """Test POST /providers/ returns 409 if resource provider already exists."""
    err_msg = "Error message"
    data = {**provider_data, "site_admins": [str(uuid.uuid4())]}
    mock_settings = MagicMock()
    sub_app_v1.dependency_overrides[get_settings] = lambda: mock_settings

    with patch(
        "fed_mgr.v1.providers.endpoints.add_provider",
        side_effect=ConflictError(err_msg),
    ) as mock_create:
        resp = client.post("/api/v1/providers/", json=data)
        mock_create.assert_called_once_with(
            session=session,
            provider=ProviderCreate(**data),
            created_by=current_user,
            secret_key=mock_settings.SECRET_KEY,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


def test_get_providers_success(client, session, provider_data):
    """Test GET /providers/ returns paginated resource provider list."""
    with patch(
        "fed_mgr.v1.providers.endpoints.get_providers", return_value=([], 0)
    ) as mock_get:
        resp = client.get("/api/v1/providers/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 0
        assert "page" in resp.json()
        assert "links" in resp.json()

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    provider1 = Provider(
        **provider_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id
    )
    with patch(
        "fed_mgr.v1.providers.endpoints.get_providers", return_value=([provider1], 1)
    ) as mock_get:
        resp = client.get("/api/v1/providers/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 1
        assert "page" in resp.json()
        assert "links" in resp.json()

    provider2 = Provider(
        **provider_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id
    )
    with patch(
        "fed_mgr.v1.providers.endpoints.get_providers",
        return_value=([provider1, provider2], 2),
    ) as mock_get:
        resp = client.get("/api/v1/providers/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 2
        assert "page" in resp.json()
        assert "links" in resp.json()


def test_get_provider_success(client, provider_dep):
    """Test GET /providers/{provider_id} returns resource provider if found."""
    resp = client.get(f"/api/v1/providers/{provider_dep.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(provider_dep.id)


def test_get_provider_not_found(client):
    """Test GET /providers/{provider_id} returns 404 if not found."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.get(f"/api/v1/providers/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"Provider with ID '{fake_id}' does not exist"


def test_edit_provider_success(client, session, current_user):
    """Test PATCH /providers/{provider_id} returns 204 on successful update."""
    fake_id = uuid.uuid4()
    new_data = {"name": "New name"}
    mock_settings = MagicMock()
    sub_app_v1.dependency_overrides[get_settings] = lambda: mock_settings

    with patch(
        "fed_mgr.v1.providers.endpoints.update_provider", return_value=None
    ) as mock_edit:
        resp = client.patch(f"/api/v1/providers/{fake_id}", json=new_data)
        mock_edit.assert_called_once_with(
            session=session,
            provider_id=fake_id,
            new_provider=ProviderUpdate(**new_data),
            updated_by=current_user,
            secret_key=mock_settings.SECRET_KEY,
        )
        assert resp.status_code == 204


def test_edit_provider_not_found(client, session, current_user):
    """Test PATCH /providers/{provider_id} returns 404 if not found."""
    fake_id = uuid.uuid4()
    err_msg = "Error err_msg"
    new_data = {"name": "New name"}
    mock_settings = MagicMock()
    sub_app_v1.dependency_overrides[get_settings] = lambda: mock_settings

    with patch(
        "fed_mgr.v1.providers.endpoints.update_provider",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.patch(f"/api/v1/providers/{fake_id}", json=new_data)
        mock_edit.assert_called_once_with(
            session=session,
            provider_id=fake_id,
            new_provider=ProviderUpdate(**new_data),
            updated_by=current_user,
            secret_key=mock_settings.SECRET_KEY,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


def test_edit_provider_conflict(client, session, current_user):
    """Test PATCH /providers/{provider_id} returns 409 if conflict error occurs."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"
    new_data = {"name": "New name"}
    mock_settings = MagicMock()
    sub_app_v1.dependency_overrides[get_settings] = lambda: mock_settings

    with patch(
        "fed_mgr.v1.providers.endpoints.update_provider",
        side_effect=ConflictError(err_msg),
    ) as mock_edit:
        resp = client.patch(f"/api/v1/providers/{fake_id}", json=new_data)
        mock_edit.assert_called_once_with(
            session=session,
            provider_id=fake_id,
            new_provider=ProviderUpdate(**new_data),
            updated_by=current_user,
            secret_key=mock_settings.SECRET_KEY,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


def test_delete_provider_success(client, session, current_user, provider_dep):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    with patch(
        "fed_mgr.v1.providers.endpoints.revoke_provider", return_value=None
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}")
        mock_delete.assert_called_once_with(
            session=session, updated_by=current_user, provider=provider_dep
        )
        assert resp.status_code == 204


def test_delete_not_existing_provider_success(client, current_user):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    fake_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.endpoints.revoke_provider", return_value=None
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{fake_id}")
        mock_delete.assert_not_called()
        assert resp.status_code == 204


def test_delete_provider_fail(client, session, current_user, provider_dep):
    """Test DELETE /providers/{provider_id} returns 400 on fail."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.endpoints.revoke_provider",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}")
        mock_delete.assert_called_once_with(
            session=session, updated_by=current_user, provider=provider_dep
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


def test_assign_site_tester(client, session, current_user, provider_dep):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    tester_id = uuid.uuid4()
    provider_dep.status = ProviderStatus.submitted
    with patch(
        "fed_mgr.v1.providers.endpoints.add_site_testers", return_value=provider_dep
    ) as mock_add:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/testers", json={"id": str(tester_id)}
        )
        mock_add.assert_called_once_with(
            session=session,
            provider=provider_dep,
            user_ids=[tester_id],
            updated_by=current_user,
        )
        assert resp.status_code == 200
        assert resp.json() is None


def test_assign_site_tester_provider_not_found(client, current_user):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    fake_provider_id = uuid.uuid4()
    tester_id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.endpoints.add_site_testers") as mock_add:
        resp = client.post(
            f"/api/v1/providers/{fake_provider_id}/testers", json={"id": str(tester_id)}
        )
        mock_add.assert_not_called()
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert (
            resp.json()["detail"]
            == f"Provider with ID '{fake_provider_id!s}' does not exist"
        )


@pytest.mark.parametrize("status", [ProviderStatus.draft, ProviderStatus.ready])
def test_assign_site_tester_fail_wrong_state(
    client, current_user, provider_dep, status
):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    tester_id = uuid.uuid4()
    provider_dep.status = status
    with patch("fed_mgr.v1.providers.endpoints.add_site_testers") as mock_add:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/testers", json={"id": str(tester_id)}
        )
        mock_add.assert_not_called()
        assert resp.status_code == 400
        assert resp.json()["status"] == 400
        assert (
            resp.json()["detail"]
            == f"Provider with ID '{provider_dep.id!s}' is in a state not "
            f"accepting site testers (current state: '{provider_dep.status.name}')"
        )


def test_remove_site_tester(client, session, current_user, provider_dep):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    tester_id = uuid.uuid4()
    provider_dep.status = ProviderStatus.submitted
    provider_dep.site_testers = [MagicMock(), MagicMock()]
    with patch(
        "fed_mgr.v1.providers.endpoints.remove_site_testers", return_value=provider_dep
    ) as mock_del:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/testers/{tester_id}")
        mock_del.assert_called_once_with(
            session=session,
            provider=provider_dep,
            user_ids=[tester_id],
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_remove_site_tester_provider_not_found(client, current_user):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    fake_provider_id = uuid.uuid4()
    tester_id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.endpoints.remove_site_testers") as mock_del:
        resp = client.delete(
            f"/api/v1/providers/{fake_provider_id}/testers/{tester_id}"
        )
        mock_del.assert_not_called()
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert (
            resp.json()["detail"]
            == f"Provider with ID '{fake_provider_id!s}' does not exist"
        )


@pytest.mark.parametrize(
    "status",
    [
        ProviderStatus.draft,
        ProviderStatus.ready,
        ProviderStatus.submitted,
        ProviderStatus.deprecated,
        ProviderStatus.removed,
    ],
)
def test_remove_last_site_tester(client, session, current_user, provider_dep, status):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    tester_id = uuid.uuid4()
    provider_dep.status = status
    provider_dep.site_testers = [MagicMock()]
    with patch("fed_mgr.v1.providers.endpoints.remove_site_testers") as mock_del:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/testers/{tester_id}")
        mock_del.assert_called_once_with(
            session=session,
            provider=provider_dep,
            user_ids=[tester_id],
            updated_by=current_user,
        )
        assert resp.status_code == 204


@pytest.mark.parametrize(
    "status",
    [
        ProviderStatus.evaluation,
        ProviderStatus.active,
        ProviderStatus.degraded,
        ProviderStatus.maintenance,
        ProviderStatus.re_evaluation,
    ],
)
def test_leave_at_least_one_site_tester_when_mandatory(
    client, session, current_user, provider_dep, status
):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    tester_id = uuid.uuid4()
    provider_dep.status = status
    provider_dep.site_testers = [MagicMock(), MagicMock()]
    with patch("fed_mgr.v1.providers.endpoints.remove_site_testers") as mock_del:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/testers/{tester_id}")
        mock_del.assert_called_once_with(
            session=session,
            provider=provider_dep,
            user_ids=[tester_id],
            updated_by=current_user,
        )
        assert resp.status_code == 204


@pytest.mark.parametrize(
    "status",
    [
        ProviderStatus.evaluation,
        ProviderStatus.active,
        ProviderStatus.degraded,
        ProviderStatus.maintenance,
        ProviderStatus.re_evaluation,
    ],
)
def test_fail_to_remove_last_site_tester(client, current_user, provider_dep, status):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    tester_id = uuid.uuid4()
    provider_dep.status = status
    provider_dep.site_testers = [MagicMock()]
    with patch("fed_mgr.v1.providers.endpoints.remove_site_testers") as mock_del:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/testers/{tester_id}")
        mock_del.assert_not_called()
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert (
            "The last site tester can be removed only from providers in the following "
            "states:" in resp.json()["detail"]
        )


def test_assign_site_admin(client, session, current_user, provider_dep):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    admin_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.endpoints.add_site_admins", return_value=provider_dep
    ) as mock_add:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/admins", json={"id": str(admin_id)}
        )
        mock_add.assert_called_once_with(
            session=session,
            provider=provider_dep,
            user_ids=[admin_id],
            updated_by=current_user,
        )
        assert resp.status_code == 200
        assert resp.json() is None


def test_assign_site_admin_provider_not_found(client, current_user):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    fake_provider_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.endpoints.add_site_admins") as mock_add:
        resp = client.post(
            f"/api/v1/providers/{fake_provider_id}/admins", json={"id": str(admin_id)}
        )
        mock_add.assert_not_called()
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert (
            resp.json()["detail"]
            == f"Provider with ID '{fake_provider_id!s}' does not exist"
        )


def test_remove_site_admin(client, session, current_user, provider_dep):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    admin_id = uuid.uuid4()
    provider_dep.site_admins = [MagicMock(), MagicMock()]
    with patch(
        "fed_mgr.v1.providers.endpoints.remove_site_admins", return_value=provider_dep
    ) as mock_del:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/admins/{admin_id}")
        mock_del.assert_called_once_with(
            session=session,
            provider=provider_dep,
            user_ids=[admin_id],
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_remove_site_admin_provider_not_found(client, current_user):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    fake_provider_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.endpoints.remove_site_admins") as mock_del:
        resp = client.delete(f"/api/v1/providers/{fake_provider_id}/admins/{admin_id}")
        mock_del.assert_not_called()
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert (
            resp.json()["detail"]
            == f"Provider with ID '{fake_provider_id!s}' does not exist"
        )


def test_fail_to_remove_last_site_admin(client, current_user, provider_dep):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    admin_id = uuid.uuid4()
    provider_dep.site_admins = [MagicMock()]
    with patch("fed_mgr.v1.providers.endpoints.remove_site_admins") as mock_del:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/admins/{admin_id}")
        mock_del.assert_not_called()
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert (
            resp.json()["detail"]
            == f"This is the last site admin for provider with ID '{provider_dep.id}'"
        )


# def test_update_provider_state_success(client, monkeypatch):
#     """Test PUT /providers/{provider_id}/change_state/{next_state} returns 200."""
#     fake_id = str(uuid.uuid4())
#     next_state = ProviderStatus.submitted.value

#     class FakeProvider:
#         id = fake_id
#         status = ProviderStatus.draft

#     def fake_get_provider(provider_id, session=None):
#         return FakeProvider()

#     sub_app_v1.dependency_overrides[get_provider] = fake_get_provider

#     monkeypatch.setattr(
#         "fed_mgr.v1.providers.endpoints.change_provider_state", lambda: None
#     )

#     resp = client.put(f"/api/v1/providers/{fake_id}/change_state/{next_state}")
#     assert resp.status_code == 200
#     sub_app_v1.dependency_overrides = {}


# def test_update_provider_state_forbidden(client, monkeypatch):
#     """Test PUT /providers/{provider_id}/change_state/{next_state} returns 400."""
#     fake_id = str(uuid.uuid4())
#     next_state = ProviderStatus.ready.value

#     class FakeProvider:
#         id = fake_id
#         status = ProviderStatus.draft

#     def fake_get_provider(provider_id, session=None):
#         return FakeProvider()

#     sub_app_v1.dependency_overrides[get_provider] = fake_get_provider

#     def fake_change_provider_state(**kwargs):
#         raise ProviderStateChangeError(ProviderStatus.draft, ProviderStatus.ready)

#     monkeypatch.setattr(
#         "fed_mgr.v1.providers.endpoints.change_provider_state",
#         fake_change_provider_state,
#     )

#     resp = client.put(f"/api/v1/providers/{fake_id}/change_state/{next_state}")
#     assert resp.status_code == 400
#     assert "forbidden transition" in resp.json()["detail"]
#     sub_app_v1.dependency_overrides = {}


# def test_update_provider_not_existing_state(client, monkeypatch):
#     """Test PUT /providers/{provider_id}/change_state/{next_state} returns 422."""
#     fake_id = str(uuid.uuid4())
#     next_state = 1000  # Invalid state value

#     class FakeProvider:
#         id = fake_id
#         status = ProviderStatus.draft

#     def fake_get_provider(provider_id, session=None):
#         return FakeProvider()

#     sub_app_v1.dependency_overrides[get_provider] = fake_get_provider

#     def fake_change_provider_state(**kwargs):
#         raise ProviderStateError("forbidden transition")

#     monkeypatch.setattr(
#         "fed_mgr.v1.providers.endpoints.change_provider_state",
#         fake_change_provider_state,
#     )

#     resp = client.put(f"/api/v1/providers/{fake_id}/change_state/{next_state}")
#     assert resp.status_code == 422
#     assert "Input should be " in resp.json()["detail"][0]["msg"]
#     sub_app_v1.dependency_overrides = {}
