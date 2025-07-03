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

from fed_mgr.exceptions import ProviderStateChangeError, UserNotFoundError
from fed_mgr.v1.models import Provider
from fed_mgr.v1.providers.crud import (
    add_provider,
    change_provider_state,
    check_site_admins_exist,
    delete_provider,
    get_provider,
    get_providers,
    update_provider,
)
from fed_mgr.v1.providers.schemas import ProviderStatus


class DummyProviderCreate:
    """Dummy Provider with the site admins attribute."""

    def __init__(self, site_admins):
        """Initialize the object with the list of site admins."""
        self.site_admins = site_admins


def test_get_provider_found(session):
    """Test get_provider returns the Provider if found."""
    provider_id = uuid.uuid4()
    expected_provider = MagicMock()
    with patch(
        "fed_mgr.v1.providers.crud.get_item",
        return_value=expected_provider,
    ) as mock_get_item:
        result = get_provider(session=session, provider_id=provider_id)
        assert result == expected_provider
        mock_get_item.assert_called_once_with(
            session=session, entity=Provider, item_id=provider_id
        )


def test_get_provider_not_found(session):
    """Test get_provider returns None if Provider not found."""
    provider_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_provider(session=session, provider_id=provider_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=Provider, item_id=provider_id
        )


def test_get_providers(session):
    """Test get_providers calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_providers(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=Provider, skip=0, limit=10, sort="name"
        )


@patch("fed_mgr.v1.providers.crud.add_item")
@patch("fed_mgr.v1.providers.crud.get_user")
def test_add_provider_calls_add_item(mock_get_user, mock_add_item, session):
    """Test add_provider calls add_item with correct arguments."""
    provider = MagicMock()
    created_by = MagicMock()
    created_by.id = uuid.uuid4()
    provider.site_admins = [created_by]
    expected_item = MagicMock()
    mock_add_item.return_value = expected_item
    mock_get_user.return_value = created_by

    result = add_provider(session=session, provider=provider, created_by=created_by)
    assert result == expected_item
    mock_add_item.assert_called_once_with(
        session=session,
        entity=Provider,
        created_by=created_by.id,
        updated_by=created_by.id,
        site_admins=[created_by],
        **provider.model_dump(),
    )


@patch("fed_mgr.v1.providers.crud.check_site_admins_exist")
def test_add_provider_user_not_found(mock_check_admins, session):
    """Test add_provider raises UserNotFoundError if site admin not found."""
    provider = MagicMock()
    created_by = MagicMock()
    created_by.id = uuid.uuid4()
    mock_check_admins.side_effect = UserNotFoundError("user not found")
    with pytest.raises(UserNotFoundError) as exc:
        add_provider(
            session=session,
            provider=provider,
            created_by=created_by,
        )
    assert "user not found" in str(exc.value)


@patch("fed_mgr.v1.providers.crud.update_item")
@patch("fed_mgr.v1.providers.crud.get_user")
def test_update_provider_calls_update_item(mock_get_user, mock_update_item, session):
    """Test update_provider calls update_item with correct arguments."""
    provider_id = uuid.uuid4()
    new_provider = MagicMock()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    site_admin = MagicMock()
    new_provider.site_admins = [site_admin]
    mock_get_user.return_value = site_admin

    update_provider(
        session=session,
        provider_id=provider_id,
        new_provider=new_provider,
        updated_by=updated_by,
    )
    mock_update_item.assert_called_once_with(
        session=session,
        entity=Provider,
        item_id=provider_id,
        updated_by=updated_by.id,
        site_admins=[site_admin],
        **new_provider.model_dump(exclude={"site_admins"}, exclude_none=True),
    )


@patch("fed_mgr.v1.providers.crud.update_item")
def test_update_provider_calls_update_item_empty_site_admins(mock_update_item, session):
    """Test update_provider omits site_admins if empty."""
    provider_id = uuid.uuid4()
    new_provider = MagicMock()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    new_provider.site_admins = None
    update_provider(
        session=session,
        provider_id=provider_id,
        new_provider=new_provider,
        updated_by=updated_by,
    )
    mock_update_item.assert_called_once_with(
        session=session,
        entity=Provider,
        item_id=provider_id,
        updated_by=updated_by.id,
        **new_provider.model_dump(exclude_none=True),
    )


@patch("fed_mgr.v1.providers.crud.check_site_admins_exist")
def test_update_provider_user_not_found(mock_check_admins, session):
    """Test update_provider raises UserNotFoundError if site admin not found."""
    provider_id = uuid.uuid4()
    new_provider = MagicMock()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    mock_check_admins.side_effect = UserNotFoundError("user not found")
    with pytest.raises(UserNotFoundError) as exc:
        update_provider(
            session=session,
            provider_id=provider_id,
            new_provider=new_provider,
            updated_by=updated_by,
        )
    assert "user not found" in str(exc.value)


def test_delete_provider_calls_delete_item(session):
    """Test delete_provider calls delete_item with correct arguments."""
    provider_id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.crud.delete_item") as mock_delete_item:
        delete_provider(session=session, provider_id=provider_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=Provider, item_id=provider_id
        )


def test_check_site_admins_exist_all_found():
    """Test check_site_admins_exist returns list of users when site user IDs exist.

    This test mocks the database session and the get_user function to simulate the
    presence of all site admin users.

    It verifies that:
    - check_site_admins_exist returns the correct list of user objects corresponding to
        the provided user IDs.
    - get_user is called exactly once for each user ID.
    - Each call to get_user is made with the correct user_id and session arguments.
    """
    session = MagicMock()
    user_ids = [uuid.uuid4(), uuid.uuid4()]
    users = [MagicMock(id=user_ids[0]), MagicMock(id=user_ids[1])]
    provider = DummyProviderCreate(site_admins=user_ids)

    with patch(
        "fed_mgr.v1.providers.crud.get_user", side_effect=users
    ) as mock_get_user:
        result = check_site_admins_exist(session=session, provider=provider)
        assert result == users
        assert mock_get_user.call_count == 2
        for idx, call in enumerate(mock_get_user.call_args_list):
            assert call.kwargs["user_id"] == user_ids[idx]
            assert call.kwargs["session"] == session


def test_check_site_admins_exist_user_not_found():
    """Test check_site_admins_exist raises a UserNotFoundError.

    Raise when at least one user ID in the provider's `site_admins` list does not
    correspond to an existing user.

    This test mocks the `get_user` function to simulate the scenario where the first
    user is found and the second user is not found (returns `None`). It asserts that
    the exception message contains the ID of the missing user.
    """
    session = MagicMock()
    user_ids = [uuid.uuid4(), uuid.uuid4()]
    provider = DummyProviderCreate(site_admins=user_ids)

    # First user found, second user not found (returns None)
    with patch("fed_mgr.v1.providers.crud.get_user", side_effect=[MagicMock(), None]):
        with pytest.raises(UserNotFoundError) as exc:
            check_site_admins_exist(session=session, provider=provider)
        assert f"User with ID '{user_ids[1]}" in str(exc.value)


def test_check_site_admins_exist_empty_list():
    """Test that check_site_admins_exist returns an empty list.

    Does not call get_user when the provider's site_admins list is empty.
    """
    session = MagicMock()
    provider = DummyProviderCreate(site_admins=[])
    with patch("fed_mgr.v1.providers.crud.get_user") as mock_get_user:
        result = check_site_admins_exist(session=session, provider=provider)
        assert result == []
        mock_get_user.assert_not_called()


@pytest.mark.parametrize(
    "current_status,next_status",
    [
        (ProviderStatus.draft, ProviderStatus.submitted),
        (ProviderStatus.submitted, ProviderStatus.ready),
        (ProviderStatus.ready, ProviderStatus.evaluation),
        (ProviderStatus.evaluation, ProviderStatus.pre_production),
        (ProviderStatus.pre_production, ProviderStatus.active),
        (ProviderStatus.active, ProviderStatus.deprecated),
        (ProviderStatus.deprecated, ProviderStatus.removed),
        (ProviderStatus.degraded, ProviderStatus.maintenance),
        (ProviderStatus.maintenance, ProviderStatus.re_evaluation),
        (ProviderStatus.re_evaluation, ProviderStatus.active),
    ],
)
def test_change_provider_state_valid_transition(session, current_status, next_status):
    """Test change_provider_state allows valid state transitions."""
    db_provider = MagicMock()
    db_provider.status = current_status
    provider_id = uuid.uuid4()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    with (
        patch(
            "fed_mgr.v1.providers.crud.get_item", return_value=db_provider
        ) as get_item_mock,
        patch("fed_mgr.v1.providers.crud.update_item") as update_item_mock,
    ):
        change_provider_state(
            session=session,
            provider_id=provider_id,
            next_state=next_status,
            updated_by=updated_by,
        )
        get_item_mock.assert_called_once_with(
            session=session, entity=Provider, item_id=provider_id
        )
        update_item_mock.assert_called_once_with(
            session=session,
            entity=Provider,
            item_id=provider_id,
            updated_by=updated_by.id,
            status=next_status,
        )


@patch("fed_mgr.v1.providers.crud.get_item")
@patch("fed_mgr.v1.providers.crud.update_item")
def test_change_provider_state_same_state_no_update(
    update_item_mock, get_item_mock, session
):
    """Test change_provider_state is idempotent."""
    db_provider = MagicMock()
    db_provider.status = ProviderStatus.active
    provider_id = uuid.uuid4()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    get_item_mock.return_value = db_provider
    change_provider_state(
        session=session,
        provider_id=provider_id,
        next_state=ProviderStatus.active,
        updated_by=updated_by,
    )
    get_item_mock.assert_called_once()
    update_item_mock.assert_called_once_with(
        session=session,
        entity=Provider,
        item_id=provider_id,
        updated_by=updated_by.id,
        status=ProviderStatus.active,
    )


@pytest.mark.parametrize(
    "current_status,next_status",
    [
        (ProviderStatus.draft, ProviderStatus.ready),
        (ProviderStatus.active, ProviderStatus.submitted),
        (ProviderStatus.removed, ProviderStatus.active),
        (ProviderStatus.deprecated, ProviderStatus.active),
    ],
)
def test_change_provider_state_invalid_transition_raises(
    session, current_status, next_status
):
    """Test that change_provider_state raises an error for invalid state transitions."""
    db_provider = MagicMock()
    db_provider.status = current_status
    provider_id = uuid.uuid4()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.crud.get_item", return_value=db_provider):
        with pytest.raises(ProviderStateChangeError) as exc:
            change_provider_state(
                session=session,
                provider_id=provider_id,
                next_state=next_status,
                updated_by=updated_by,
            )
        assert (
            f"Transition from state '{current_status}' to state '{next_status}' is "
            "forbidden" in str(exc.value)
        )
