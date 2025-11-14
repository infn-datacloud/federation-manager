"""Integration tests for fed_mgr.v1.identity_providers.slas.endpoints.

Tests in this file:
- test_options_slas
- test_connect_project_success
- test_connect_project_conflict
- test_connect_project_not_null_error
- test_connect_project_parent_idp_not_found
- test_get_project_sla_conn_success
- test_get_sla_success
- test_get_sla_not_found
- test_edit_sla_success
- test_edit_sla_not_found
- test_edit_sla_conflict
- test_edit_sla_not_null_error
- test_delete_proj_conn_success
"""

import uuid
from unittest.mock import patch

from fed_mgr.exceptions import DeleteFailedError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.identity_providers.user_groups.crud import get_user_group
from fed_mgr.v1.identity_providers.user_groups.slas.crud import get_sla
from fed_mgr.v1.models import Project
from fed_mgr.v1.providers.projects.crud import get_project


# OPTIONS endpoint
def test_options_slas_parent_idp_not_found(client, user_group_dep, sla_dep):
    """Test OPTIONS returns 404 if parent_user_group is None."""
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.options(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_options_slas_parent_user_group_not_found(client, idp_dep, sla_dep):
    """Test OPTIONS returns 404 if parent_user_group is None."""
    fake_user_group_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_user_group] = lambda: None

    resp = client.options(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_user_group_id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"User group with ID '{fake_user_group_id}' does not exist"
    )


def test_options_slas_parent_sla_not_found(client, idp_dep, user_group_dep):
    """Test OPTIONS returns 404 if parent_user_group is None."""
    fake_sla_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_sla] = lambda: None

    resp = client.options(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{fake_sla_id}/projects/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"SLA with ID '{fake_sla_id}' does not exist"


def test_options_slas(client, idp_dep, user_group_dep, sla_dep):
    """Test OPTIONS /idps/{idp_id}/user-groups/ returns 204 and Allow header."""
    resp = client.options(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_connect_project_parent_idp_not_found(client, user_group_dep, sla_dep):
    """Test POST returns 404 if parent_user_group is None."""
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/",
        json={"project_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_connect_project_parent_user_group_not_found(client, idp_dep, sla_dep):
    """Test POST returns 404 if parent_user_group is None."""
    fake_user_group_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_user_group] = lambda: None

    resp = client.post(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_user_group_id}/slas/{sla_dep.id}/projects/",
        json={"project_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"User group with ID '{fake_user_group_id}' does not exist"
    )


def test_connect_project_parent_sla_not_found(client, idp_dep, user_group_dep):
    """Test POST returns 404 if parent_user_group is None."""
    fake_sla_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_sla] = lambda: None

    resp = client.post(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{fake_sla_id}/projects/",
        json={"project_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"SLA with ID '{fake_sla_id}' does not exist"


def test_connect_project_target_project_not_found(
    client, session, current_user, idp_dep, user_group_dep, sla_dep
):
    """Test POST returns 404 if parent_user_group is None."""
    fake_project_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.projects.endpoints.get_project",
        return_value=None,
    ) as mock_get:
        resp = client.post(
            f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/",
            json={"project_id": str(fake_project_id)},
        )
        mock_get.assert_called_once_with(session=session, project_id=fake_project_id)
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert (
            resp.json()["detail"]
            == f"Project with ID '{fake_project_id}' does not exist"
        )


def test_connect_project_success(
    client, session, current_user, idp_dep, user_group_dep, sla_dep, project_dep
):
    """Test POST creates a user group and returns 201 with id."""
    with (
        patch(
            "fed_mgr.v1.identity_providers.user_groups.slas.projects.endpoints.get_project",
            return_value=project_dep,
        ) as mock_get,
        patch(
            "fed_mgr.v1.identity_providers.user_groups.slas.projects.endpoints.connect_proj_to_sla",
            return_value=None,
        ) as mock_create,
    ):
        resp = client.post(
            f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/",
            json={"project_id": str(project_dep.id)},
        )
        mock_get.assert_called_once_with(session=session, project_id=project_dep.id)
        mock_create.assert_called_once_with(
            session=session, sla=sla_dep, project=project_dep, updated_by=current_user
        )
        assert resp.status_code == 200
        assert resp.json() is None


# GET (list) endpoint
def test_get_project_sla_conn_parent_idp_not_found(client, user_group_dep, sla_dep):
    """Test GET returns 404 if parent_user_group is None."""
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_get_project_sla_conn_parent_user_group_not_found(client, idp_dep, sla_dep):
    """Test GET returns 404 if parent_user_group is None."""
    fake_user_group_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_user_group] = lambda: None

    resp = client.get(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_user_group_id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"User group with ID '{fake_user_group_id}' does not exist"
    )


def test_get_project_sla_conn_parent_sla_not_found(client, idp_dep, user_group_dep):
    """Test GET returns 404 if parent_user_group is None."""
    fake_sla_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_sla] = lambda: None

    resp = client.get(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{fake_sla_id}/projects/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"SLA with ID '{fake_sla_id}' does not exist"


def test_get_project_sla_conn_success(
    client, session, idp_dep, user_group_dep, sla_dep, project_data
):
    """Test GET returns paginated user group list."""
    resp = client.get(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert len(resp.json()["data"]) == 0
    assert "page" in resp.json()
    assert "links" in resp.json()

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    proj1 = Project(
        **project_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id
    )
    sla_dep.projects = [proj1]
    resp = client.get(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "data" in resp.json()
    assert len(resp.json()["data"]) == 1
    assert "page" in resp.json()
    assert "links" in resp.json()

    proj2 = Project(
        **project_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id
    )
    sla_dep.projects = [proj1, proj2]
    resp = client.get(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert "data" in resp.json()
    assert len(resp.json()["data"]) == 2
    assert "page" in resp.json()
    assert "links" in resp.json()


# DELETE endpoint
def test_delete_proj_conn_parent_idp_not_found(client, user_group_dep, sla_dep):
    """Test DELETE returns 404 if parent_user_group is None."""
    fake_id = uuid.uuid4()
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.delete(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/{fake_id}"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_delete_proj_conn_parent_user_group_not_found(client, idp_dep, sla_dep):
    """Test DELETE returns 404 if parent_user_group is None."""
    fake_id = uuid.uuid4()
    fake_user_group_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_user_group] = lambda: None

    resp = client.delete(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_user_group_id}/slas/{sla_dep.id}/projects/{fake_id}"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"User group with ID '{fake_user_group_id}' does not exist"
    )


def test_delete_proj_conn_parent_sla_not_found(client, idp_dep, user_group_dep):
    """Test DELETE returns 404 if parent_user_group is None."""
    fake_id = uuid.uuid4()
    fake_sla_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_sla] = lambda: None

    resp = client.delete(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{fake_sla_id}/projects/{fake_id}"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"SLA with ID '{fake_sla_id}' does not exist"


def test_delete_missing_project_success(
    client, current_user, idp_dep, user_group_dep, sla_dep
):
    """Test DELETE returns 204 on success."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_project] = lambda: None

    resp = client.delete(
        f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/{fake_id}"
    )
    assert resp.status_code == 204


def test_delete_proj_conn_success(
    client, session, current_user, idp_dep, user_group_dep, sla_dep, project_dep
):
    """Test DELETE returns 204 on success."""
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.projects.endpoints.disconnect_proj_from_sla",
        return_value=None,
    ) as mock_delete:
        resp = client.delete(
            f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/{project_dep.id}"
        )
        mock_delete.assert_called_once_with(
            session=session, updated_by=current_user, project=project_dep
        )
        assert resp.status_code == 204


def test_delete_proj_conn_fail(
    client, session, current_user, idp_dep, user_group_dep, sla_dep, project_dep
):
    """Test DELETE returns 400 on fail."""
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.projects.endpoints.disconnect_proj_from_sla",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(
            f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}/slas/{sla_dep.id}/projects/{project_dep.id}"
        )
        mock_delete.assert_called_once_with(
            session=session, updated_by=current_user, project=project_dep
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
