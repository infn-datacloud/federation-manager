"""Unit tests for fed_mgr.v1.providers.crud.

Tests in this file:
- test_get_provider_calls_get_item
- test_get_providers_calls_get_items
- test_add_provider_calls_add_item
- test_update_provider_calls_update_item
- test_delete_provider_calls_delete_item
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from fed_mgr.exceptions import ItemNotFoundError, ProviderStateError
from fed_mgr.v1.models import Provider, User
from fed_mgr.v1.providers.crud import (
    add_provider,
    add_site_admins,
    add_site_testers,
    check_users_exist,
    delete_provider,
    get_provider,
    get_providers,
    remove_site_admins,
    remove_site_testers,
    submit_provider,
    unsubmit_provider,
    update_provider,
)
from fed_mgr.v1.providers.schemas import ProviderCreate, ProviderStatus, ProviderUpdate
from tests.utils import random_lower_string


def test_get_provider_found(session):
    """Test get_provider returns the Provider if found."""
    provider_id = uuid.uuid4()
    expected_provider = MagicMock(spec=Provider)
    with patch(
        "fed_mgr.v1.providers.crud.get_item",
        return_value=expected_provider,
    ) as mock_get_item:
        result = get_provider(session=session, provider_id=provider_id)
        mock_get_item.assert_called_once_with(
            session=session, entity=Provider, id=provider_id
        )
        assert result == expected_provider


def test_get_provider_not_found(session):
    """Test get_provider returns None if Provider not found."""
    provider_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_provider(session=session, provider_id=provider_id)
        mock_get_item.assert_called_once_with(
            session=session, entity=Provider, id=provider_id
        )
        assert result is None


def test_get_providers(session):
    """Test get_providers calls get_items with correct arguments."""
    expected_list = [MagicMock(spec=Provider), MagicMock(spec=Provider)]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_providers(session=session, skip=0, limit=10, sort="name")
        mock_get_items.assert_called_once_with(
            session=session, entity=Provider, skip=0, limit=10, sort="name"
        )
        assert result == (expected_list, expected_count)


def test_add_provider(session):
    """Test add_provider calls add_item with correct arguments."""
    created_by = MagicMock(spec=User)
    created_by.id = uuid.uuid4()
    provider = MagicMock(spec=ProviderCreate)
    provider.rally_password = random_lower_string()
    provider.site_admins = [created_by.id]
    expected_item = MagicMock(spec=Provider)
    with (
        patch(
            "fed_mgr.v1.providers.crud.add_item", return_value=expected_item
        ) as mock_add_item,
        patch(
            "fed_mgr.v1.providers.crud.get_user", return_value=created_by
        ) as mock_get_user,
    ):
        result = add_provider(
            session=session,
            provider=provider,
            created_by=created_by,
            secret_key=random_lower_string(),
        )
        mock_add_item.assert_called_once_with(
            session=session,
            entity=Provider,
            created_by=created_by,
            updated_by=created_by,
            site_admins=[created_by],
            **provider.model_dump(),
        )
        mock_get_user.assert_called_once_with(session=session, user_id=created_by.id)
        assert result == expected_item


def test_add_provider_user_not_found(session):
    """Test add_provider raises ItemNotFoundError if site admin not found."""
    created_by = MagicMock(spec=User)
    created_by.id = uuid.uuid4()
    provider = MagicMock(spec=ProviderCreate)
    provider.site_admins = [created_by.id]
    with patch("fed_mgr.v1.providers.crud.get_user", return_value=None):
        with pytest.raises(ItemNotFoundError, match=f"User with ID '{created_by.id}"):
            add_provider(
                session=session,
                provider=provider,
                created_by=created_by,
                secret_key=random_lower_string(),
            )


def test_update_provider(session):
    """Test update_provider calls update_item with correct arguments."""
    provider_id = uuid.uuid4()
    new_provider = MagicMock(spec=ProviderUpdate)
    new_provider.rally_password = random_lower_string()
    updated_by = MagicMock(spec=User)

    with (
        patch(
            "fed_mgr.v1.providers.crud.update_item", return_value=None
        ) as mock_update_item,
        patch("fed_mgr.v1.providers.crud.encrypt") as mock_encrypt,
    ):
        result = update_provider(
            session=session,
            provider_id=provider_id,
            new_provider=new_provider,
            updated_by=updated_by,
            secret_key=random_lower_string(),
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=Provider,
            id=provider_id,
            updated_by=updated_by,
            **new_provider.model_dump(exclude_none=True),
        )
        mock_encrypt.assert_called_once()
        assert result is None


def test_update_provider_no_pwd(session):
    """Test update_provider calls update_item with correct arguments."""
    provider_id = uuid.uuid4()
    new_provider = MagicMock(spec=ProviderUpdate)
    new_provider.rally_password = None
    updated_by = MagicMock(spec=User)

    with (
        patch(
            "fed_mgr.v1.providers.crud.update_item", return_value=None
        ) as mock_update_item,
        patch("fed_mgr.v1.providers.crud.encrypt") as mock_encrypt,
    ):
        result = update_provider(
            session=session,
            provider_id=provider_id,
            new_provider=new_provider,
            updated_by=updated_by,
            secret_key=random_lower_string(),
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=Provider,
            id=provider_id,
            updated_by=updated_by,
            **new_provider.model_dump(exclude_none=True),
        )
        mock_encrypt.assert_not_called()
        assert result is None


def test_delete_provider_calls_delete_item(session):
    """Test delete_provider calls delete_item with correct arguments."""
    provider_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.crud.delete_item", return_value=None
    ) as mock_delete_item:
        result = delete_provider(session=session, provider_id=provider_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=Provider, id=provider_id
        )
        assert result is None


def test_check_users_exist_all_found(session):
    """Test check_users_exist returns list of users when site user IDs exist.

    This test mocks the database session and the get_user function to simulate the
    presence of all site admin users.

    It verifies that:
    - check_users_exist returns the correct list of user objects corresponding to
        the provided user IDs.
    - get_user is called exactly once for each user ID.
    - Each call to get_user is made with the correct user_id and session arguments.
    """
    user_ids = [uuid.uuid4(), uuid.uuid4()]
    users = [MagicMock(id=user_ids[0]), MagicMock(id=user_ids[1])]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", side_effect=users
    ) as mock_get_user:
        result = check_users_exist(session=session, user_ids=user_ids)
        assert mock_get_user.call_count == 2
        for idx, call in enumerate(mock_get_user.call_args_list):
            assert call.kwargs["user_id"] == user_ids[idx]
            assert call.kwargs["session"] == session
        assert result == users


def test_check_users_exist_user_not_found():
    """Test check_users_exist raises a ItemNotFoundError.

    Raise when at least one user ID in the provider's `site_admins` list does not
    correspond to an existing user.

    This test mocks the `get_user` function to simulate the scenario where the first
    user is found and the second user is not found (returns `None`). It asserts that
    the exception message contains the ID of the missing user.
    """
    session = MagicMock()
    user_ids = [uuid.uuid4(), uuid.uuid4()]

    # First user found, second user not found (returns None)
    with patch("fed_mgr.v1.providers.crud.get_user", side_effect=[MagicMock(), None]):
        with pytest.raises(ItemNotFoundError, match=f"User with ID '{user_ids[1]}"):
            check_users_exist(session=session, user_ids=user_ids)


def test_check_users_exist_empty_list(session):
    """Test that check_users_exist returns an empty list.

    Does not call get_user when the provider's site_admins list is empty.
    """
    with patch("fed_mgr.v1.providers.crud.get_user") as mock_get_user:
        result = check_users_exist(session=session, user_ids=[])
        mock_get_user.assert_not_called()
        assert result == []


def test_add_site_testers(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_tester = MagicMock(spec=User)
    provider.site_testers = [site_tester]
    updated_by = MagicMock(spec=User)
    new_site_tester = MagicMock(spec=User)
    new_site_tester.id = uuid.uuid4()
    new_site_testers = [new_site_tester.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=new_site_tester
    ) as mock_get_user:
        result = add_site_testers(
            session=session,
            provider=provider,
            user_ids=new_site_testers,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_testers) == 2
        assert site_tester in result.site_testers
        assert new_site_tester in result.site_testers
        assert result.updated_by == updated_by


def test_add_site_testers_already_exist(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_tester = MagicMock(spec=User)
    provider.site_testers = [site_tester]
    updated_by = MagicMock(spec=User)
    new_site_testers = [site_tester.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=site_tester
    ) as mock_get_user:
        result = add_site_testers(
            session=session,
            provider=provider,
            user_ids=new_site_testers,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_testers) == 1
        assert site_tester in result.site_testers
        assert result.updated_by == updated_by


def test_remove_site_testers(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_tester = MagicMock(spec=User)
    site_tester.id = uuid.uuid4()
    provider.site_testers = [site_tester]
    updated_by = MagicMock(spec=User)
    del_site_testers = [site_tester.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=site_tester
    ) as mock_get_user:
        result = remove_site_testers(
            session=session,
            provider=provider,
            user_ids=del_site_testers,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_testers) == 0
        assert result.updated_by == updated_by


def test_remove_site_testers_missing(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_tester = MagicMock(spec=User)
    provider.site_testers = [site_tester]
    updated_by = MagicMock(spec=User)
    del_site_tester = MagicMock(spec=User)
    del_site_tester.id = uuid.uuid4()
    del_site_testers = [del_site_tester.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=del_site_tester
    ) as mock_get_user:
        result = remove_site_testers(
            session=session,
            provider=provider,
            user_ids=del_site_testers,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_testers) == 1
        assert site_tester in result.site_testers
        assert result.updated_by == updated_by


def test_add_site_admins(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_admin = MagicMock(spec=User)
    provider.site_admins = [site_admin]
    updated_by = MagicMock(spec=User)
    new_site_admin = MagicMock(spec=User)
    new_site_admin.id = uuid.uuid4()
    new_site_admins = [new_site_admin.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=new_site_admin
    ) as mock_get_user:
        result = add_site_admins(
            session=session,
            provider=provider,
            user_ids=new_site_admins,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_admins) == 2
        assert site_admin in result.site_admins
        assert new_site_admin in result.site_admins
        assert result.updated_by == updated_by


def test_add_site_admins_already_exist(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_admin = MagicMock(spec=User)
    provider.site_admins = [site_admin]
    updated_by = MagicMock(spec=User)
    new_site_admins = [site_admin.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=site_admin
    ) as mock_get_user:
        result = add_site_admins(
            session=session,
            provider=provider,
            user_ids=new_site_admins,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_admins) == 1
        assert site_admin in result.site_admins
        assert result.updated_by == updated_by


def test_remove_site_admins(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_admin = MagicMock(spec=User)
    site_admin.id = uuid.uuid4()
    del_site_admin = MagicMock(spec=User)
    del_site_admin.id = uuid.uuid4()
    provider.site_admins = [site_admin, del_site_admin]
    updated_by = MagicMock(spec=User)
    del_site_admins = [del_site_admin.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=del_site_admin
    ) as mock_get_user:
        result = remove_site_admins(
            session=session,
            provider=provider,
            user_ids=del_site_admins,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_admins) == 1
        assert site_admin in result.site_admins
        assert del_site_admin not in result.site_admins
        assert result.updated_by == updated_by


def test_remove_site_admins_empty_list(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_admin = MagicMock(spec=User)
    site_admin.id = uuid.uuid4()
    provider.site_admins = [site_admin]
    updated_by = MagicMock(spec=User)
    del_site_admins = [site_admin.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=site_admin
    ) as mock_get_user:
        with pytest.raises(ValueError, match="List must not be empty"):
            remove_site_admins(
                session=session,
                provider=provider,
                user_ids=del_site_admins,
                updated_by=updated_by,
            )
        mock_get_user.assert_called_once()


def test_remove_site_admins_missing(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    site_admin = MagicMock(spec=User)
    provider.site_admins = [site_admin]
    updated_by = MagicMock(spec=User)
    del_site_admin = MagicMock(spec=User)
    del_site_admin.id = uuid.uuid4()
    del_site_admins = [del_site_admin.id]

    with patch(
        "fed_mgr.v1.providers.crud.get_user", return_value=del_site_admin
    ) as mock_get_user:
        result = remove_site_admins(
            session=session,
            provider=provider,
            user_ids=del_site_admins,
            updated_by=updated_by,
        )
        mock_get_user.assert_called_once()
        assert len(result.site_admins) == 1
        assert site_admin in result.site_admins
        assert result.updated_by == updated_by


def test_submit_provider(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    provider.status = ProviderStatus.ready
    updated_by = MagicMock(spec=User)
    provider = submit_provider(
        session=session, provider=provider, updated_by=updated_by
    )
    assert provider.status == ProviderStatus.submitted
    assert provider.updated_by == updated_by

    # if already in submitted state, 'submit again' does nothing
    provider = submit_provider(
        session=session, provider=provider, updated_by=updated_by
    )
    assert provider.status == ProviderStatus.submitted
    assert provider.updated_by == updated_by


@pytest.mark.parametrize(
    "status",
    [
        ProviderStatus.draft,
        ProviderStatus.evaluation,
        ProviderStatus.pre_production,
        ProviderStatus.active,
        ProviderStatus.deprecated,
        ProviderStatus.removed,
        ProviderStatus.degraded,
        ProviderStatus.maintenance,
        ProviderStatus.re_evaluation,
    ],
)
def test_submit_provider_wrong_state(session, status):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    provider.status = status
    updated_by = MagicMock(spec=User)
    message = f"Transition from state '{status.name}' to state 'submitted' is forbidden"
    with pytest.raises(ProviderStateError, match=message):
        submit_provider(session=session, provider=provider, updated_by=updated_by)


def test_unsubmit_provider(session):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    provider.status = ProviderStatus.submitted
    updated_by = MagicMock(spec=User)
    provider = unsubmit_provider(
        session=session, provider=provider, updated_by=updated_by
    )
    assert provider.status == ProviderStatus.ready
    assert provider.updated_by == updated_by

    # if already in ready state, 'unsubmit again' does nothing
    provider = unsubmit_provider(
        session=session, provider=provider, updated_by=updated_by
    )
    assert provider.status == ProviderStatus.ready
    assert provider.updated_by == updated_by


@pytest.mark.parametrize(
    "status",
    [
        ProviderStatus.draft,
        ProviderStatus.evaluation,
        ProviderStatus.pre_production,
        ProviderStatus.active,
        ProviderStatus.deprecated,
        ProviderStatus.removed,
        ProviderStatus.degraded,
        ProviderStatus.maintenance,
        ProviderStatus.re_evaluation,
    ],
)
def test_unsubmit_provider_wrong_state(session, status):
    """Test update_provider calls update_item with correct arguments."""
    provider = MagicMock(spec=Provider)
    provider.status = status
    updated_by = MagicMock(spec=User)
    message = f"Transition from state '{status.name}' to state 'ready' is forbidden"
    with pytest.raises(ProviderStateError, match=message):
        unsubmit_provider(session=session, provider=provider, updated_by=updated_by)


# @pytest.mark.parametrize(
#     "current_status,next_status",
#     [
#         (ProviderStatus.draft, ProviderStatus.ready),
#         (ProviderStatus.ready, ProviderStatus.submitted),
#         (ProviderStatus.submitted, ProviderStatus.evaluation),
#         (ProviderStatus.evaluation, ProviderStatus.pre_production),
#         (ProviderStatus.pre_production, ProviderStatus.active),
#         (ProviderStatus.active, ProviderStatus.deprecated),
#         (ProviderStatus.deprecated, ProviderStatus.removed),
#         (ProviderStatus.degraded, ProviderStatus.maintenance),
#         (ProviderStatus.maintenance, ProviderStatus.re_evaluation),
#         (ProviderStatus.re_evaluation, ProviderStatus.active),
#     ],
# )
# def test_change_provider_state_valid_transition(session, current_status, next_status):
#     """Test change_provider_state allows valid state transitions."""
#     db_provider = MagicMock()
#     db_provider.status = current_status
#     updated_by = MagicMock()
#     change_provider_state(
#         session=session,
#         provider=db_provider,
#         next_state=next_status,
#         updated_by=updated_by,
#     )
#     assert db_provider.status == next_status


# def test_change_provider_state_same_state_no_update(session):
#     """Test change_provider_state is idempotent."""
#     db_provider = MagicMock()
#     db_provider.status = ProviderStatus.active
#     updated_by = MagicMock()
#     change_provider_state(
#         session=session,
#         provider=db_provider,
#         next_state=ProviderStatus.active,
#         updated_by=updated_by,
#     )
#     assert db_provider.status == ProviderStatus.active


# TODO: add tests for new functions changing state and test that they raises the error
# @pytest.mark.parametrize(
#     "current_status,next_status",
#     [
#         (ProviderStatus.draft, ProviderStatus.ready),
#         (ProviderStatus.active, ProviderStatus.submitted),
#         (ProviderStatus.removed, ProviderStatus.active),
#         (ProviderStatus.deprecated, ProviderStatus.active),
#     ],
# )
# def test_change_provider_state_invalid_transition_raises(
#     session, current_status, next_status
# ):
#     """Test that change_provider_state raises an error for invalid next state."""
#     db_provider = MagicMock()
#     db_provider.status = current_status
#     updated_by = MagicMock()
#     with pytest.raises(ProviderStateChangeError) as exc:
#         change_provider_state(
#             session=session,
#             provider=db_provider,
#             next_state=next_status,
#             updated_by=updated_by,
#         )
#     assert (
#         f"Transition from state '{current_status}' to state '{next_status}' is "
#         "forbidden" in str(exc.value)
#     )
