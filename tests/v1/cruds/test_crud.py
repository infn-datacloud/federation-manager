"""Unit tests for v1 common crud functions.

These tests cover:
- raise_from_integrity_error for NOT NULL, UNIQUE, and generic errors
- get_conditions for string, numeric, and date filters
- get_item for correct session.exec usage
- get_items for correct select/count statements and empty results
- add_item for normal, created_by, NOT NULL, and UNIQUE constraint cases
- update_item for success, no item, NOT NULL, and UNIQUE constraint cases
- delete_item for correct execution and commit
"""

import uuid
from unittest.mock import MagicMock

import pytest
import sqlalchemy
from sqlmodel import Field, SQLModel

from fed_mgr.exceptions import ConflictError, NoItemToUpdateError, NotNullError
from fed_mgr.v1.crud import (
    add_item,
    delete_item,
    get_conditions,
    get_item,
    get_items,
    raise_from_integrity_error,
    update_item,
)


class DummyEntity(SQLModel, table=True):
    """Dummy SQLModel entity for testing CRUD utility functions."""

    __name__ = "DummyEntity"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: int = Field(default=0)
    updated_at: int = Field(default=0)
    start_date: int = Field(default=0)
    end_date: int = Field(default=0)
    name: str = Field(default="foo")
    value: int = Field(default=0)


def test_raise_from_integrity_error_not_null(session, monkeypatch):
    """Test raise_from_integrity_error raises NotNullError on NOT NULL constraint."""
    # Patch split_camel_case to return a known value
    item = MagicMock()
    item.model_dump.return_value = {"name": "foo"}
    monkeypatch.setattr("fed_mgr.v1.crud.split_camel_case", lambda x: "Dummy Entity")
    error = Exception("NOT NULL constraint failed: dummyentity.name")
    error.args = ("NOT NULL constraint failed: dummyentity.name",)
    with pytest.raises(NotNullError) as exc:
        raise_from_integrity_error(
            entity=DummyEntity,
            session=session,
            item=item,
            error=error,
        )
    assert "Attribute 'name' of Dummy Entity can't be NULL" in str(exc.value)
    session.rollback.assert_called_once()


def test_raise_from_integrity_error_unique(session, monkeypatch):
    """Test raise_from_integrity_error raises ConflictError on NOT UNIQUE constraint."""
    item = MagicMock()
    item.model_dump.return_value = {"name": "foo"}
    monkeypatch.setattr("fed_mgr.v1.crud.split_camel_case", lambda x: "Dummy Entity")
    error = Exception("UNIQUE constraint failed: dummyentity.name")
    error.args = ("UNIQUE constraint failed: dummyentity.name",)
    with pytest.raises(ConflictError) as exc:
        raise_from_integrity_error(
            entity=DummyEntity,
            session=session,
            item=item,
            error=error,
        )
    assert "Dummy Entity with name 'foo' already exists" in str(exc.value)
    session.rollback.assert_called_once()


def test_raise_from_integrity_error_other_error(session, monkeypatch):
    """Test raise_from_integrity_error raises a generic error."""
    item = MagicMock()
    item.model_dump.return_value = {"name": "foo"}
    monkeypatch.setattr("fed_mgr.v1.crud.split_camel_case", lambda x: "Dummy Entity")
    error = Exception("Some other error")
    error.args = ("Some other error",)
    # Should not raise NotNullError or ConflictError
    raise_from_integrity_error(
        entity=DummyEntity,
        session=session,
        item=item,
        error=error,
    )
    session.rollback.assert_called_once()


def test_get_conditions_str_and_numeric():
    """Test get_conditions with string and numeric filters."""
    conds = get_conditions(
        entity=DummyEntity, name="bar", value=5, value_gte=1, value_lte=10
    )
    conds = [str(c) for c in conds]
    assert "lower(dummyentity.name) LIKE '%' || lower(:name_1) || '%'" in conds
    assert "dummyentity.value <= :value_1" in conds
    assert "dummyentity.value >= :value_1" in conds
    assert "dummyentity.value = :value_1" in conds


def test_get_conditions_created_updated():
    """Test get_conditions with created/updated before/after filters."""
    conds = get_conditions(
        entity=DummyEntity,
        created_before=1,
        created_after=2,
        updated_before=3,
        updated_after=4,
    )
    conds = [str(c) for c in conds]
    assert "dummyentity.created_at <= :created_at_1" in conds
    assert "dummyentity.created_at >= :created_at_1" in conds
    assert "dummyentity.updated_at <= :updated_at_1" in conds
    assert "dummyentity.updated_at >= :updated_at_1" in conds


def test_get_conditions_start_end():
    """Test get_conditions with start/end before/after filters."""
    conds = get_conditions(
        entity=DummyEntity,
        start_before=1,
        start_after=2,
        end_before=3,
        end_after=4,
    )
    conds = [str(c) for c in conds]
    assert "dummyentity.start_date <= :start_date_1" in conds
    assert "dummyentity.start_date >= :start_date_1" in conds
    assert "dummyentity.end_date <= :end_date_1" in conds
    assert "dummyentity.end_date >= :end_date_1" in conds


def test_get_conditions_unsupported_type():
    """Test get_conditions returns no condition for unsupported value types."""

    class DummyUnsupported:
        pass

    conds = get_conditions(entity=DummyEntity, unsupported=DummyUnsupported())
    assert conds == []


@pytest.mark.parametrize("item_value", ["item", None])
def test_get_item_calls_session_exec(session, item_value):
    """Test get_item calls session.exec and returns the first result or None."""
    item_id = uuid.uuid4()
    session.exec.return_value.first.return_value = item_value
    result = get_item(entity=DummyEntity, session=session, item_id=item_id)
    assert result == item_value
    session.exec.assert_called()


@pytest.mark.parametrize("order", ["ASC", "DESC"])
def test_get_items_exec_called_with_correct_statement(session, order):
    """Test get_items calls session.exec with correct select statement for items."""
    # Prepare mocks
    session.exec.side_effect = [
        MagicMock(all=lambda: ["item1", "item2"]),
        MagicMock(first=lambda: 2),
    ]
    key = "created_at"
    if order == "DESC":
        key = f"-{key}"

    # Call get_items
    items, tot = get_items(
        entity=DummyEntity, session=session, skip=5, limit=10, sort=key
    )

    # Check the first call to session.exec
    first_call_args = session.exec.call_args_list[0][0]
    statement = first_call_args[0]
    # The statement should be a select on DummyEntity with correct offset, limit, and
    # order_by
    assert hasattr(statement, "offset")
    assert hasattr(statement, "limit")
    assert hasattr(statement, "order_by")
    assert statement._limit == 10
    assert statement._offset == 5
    assert any(
        "created_at" in str(o) and order in str(o) for o in statement._order_by_clauses
    )

    # Check the second call to session.exec (for count)
    second_call_args = session.exec.call_args_list[1][0]
    count_statement = second_call_args[0]
    # The count statement should not have offset or limit
    assert not getattr(count_statement, "_limit", None)
    assert not getattr(count_statement, "_offset", None)
    assert hasattr(statement, "order_by")
    assert any(
        "created_at" in str(o) and order in str(o) for o in statement._order_by_clauses
    )

    assert items == ["item1", "item2"]
    assert tot == 2
    assert session.exec.call_count == 2


def test_get_items_returns_empty_list_and_zero_count(session):
    """Test get_items returns an empty list and zero count when no users."""
    # Prepare mocks
    session.exec.side_effect = [
        MagicMock(all=lambda: []),
        MagicMock(first=lambda: 0),
    ]

    # Call get_items
    items, tot = get_items(
        entity=DummyEntity, session=session, skip=5, limit=10, sort="-created_at"
    )

    assert items == []
    assert tot == 0
    assert session.exec.call_count == 2


def test_add_item_adds_and_commits(session):
    """Test add_item adds the entity to the session and commits."""
    item = MagicMock(spec=DummyEntity)
    item.model_dump.return_value = {"id": uuid.uuid4()}
    result = add_item(entity=DummyEntity, session=session, item=item, created_by=None)
    session.add.assert_called()
    session.commit.assert_called()
    assert isinstance(result, DummyEntity)


def test_add_item_with_created_by(session):
    """Test add_item adds the entity with a non-None created_by user and commits."""
    item = MagicMock(spec=DummyEntity)
    item.model_dump.return_value = {"id": uuid.uuid4()}
    result = add_item(
        entity=DummyEntity, session=session, item=item, created_by=uuid.uuid4()
    )
    session.add.assert_called()
    session.commit.assert_called()
    assert isinstance(result, DummyEntity)


def test_add_item_raises_not_null_error(session):
    """Test add_item raises NotNullError on NOT NULL constraint violation."""
    item = MagicMock(spec=DummyEntity)
    item.model_dump.return_value = {"id": uuid.uuid4()}

    # Simulate IntegrityError for NOT NULL constraint
    exc = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("NOT NULL constraint failed: dummyentity.name"),
    )
    exc.args = ("NOT NULL constraint failed: dummyentity.name",)
    session.add.side_effect = exc

    with pytest.raises(NotNullError) as e:
        add_item(entity=DummyEntity, session=session, item=item, created_by=None)
    assert "can't be NULL" in str(e.value)
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_add_item_raises_conflict_error(session):
    """Test add_item raises ConflictError on UNIQUE constraint violation."""
    item = MagicMock(spec=DummyEntity)
    item.model_dump.return_value = {"id": uuid.uuid4(), "name": "foo"}

    # Simulate IntegrityError for UNIQUE constraint
    exc = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("UNIQUE constraint failed: dummyentity.name"),
    )
    exc.args = ("UNIQUE constraint failed: dummyentity.name",)
    session.add.side_effect = exc

    with pytest.raises(ConflictError) as e:
        add_item(entity=DummyEntity, session=session, item=item, created_by=None)
    assert "already exists" in str(e.value)
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_update_item_success(session):
    """Test update_item successfully updates and commits when rowcount > 0."""
    item_id = uuid.uuid4()
    new_data = MagicMock()
    new_data.model_dump.return_value = {"name": "newname"}

    # Mock session.exec to return an object with rowcount > 0
    exec_result = MagicMock()
    exec_result.rowcount = 1
    session.exec.return_value = exec_result

    update_item(entity=DummyEntity, session=session, item_id=item_id, new_data=new_data)
    session.exec.assert_called()
    session.commit.assert_called_once()


def test_update_item_no_item_to_update(session):
    """Test update_item raises NoItemToUpdateError when rowcount == 0."""
    item_id = uuid.uuid4()
    new_data = MagicMock()
    new_data.model_dump.return_value = {"name": "newname"}

    # Mock session.exec to return an object with rowcount = 0
    exec_result = MagicMock()
    exec_result.rowcount = 0
    session.exec.return_value = exec_result

    with pytest.raises(NoItemToUpdateError) as exc:
        update_item(
            entity=DummyEntity, session=session, item_id=item_id, new_data=new_data
        )
    assert "Dummy Entity" in str(exc.value) or "DummyEntity" in str(exc.value)
    session.exec.assert_called()
    session.commit.assert_not_called()


def test_update_item_integrity_error_not_null(monkeypatch, session):
    """Test update_item raises NotNullError on NOT NULL constraint violation."""
    item_id = uuid.uuid4()
    new_data = MagicMock()
    new_data.model_dump.return_value = {"name": None}

    # Simulate IntegrityError for NOT NULL constraint
    exc = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("NOT NULL constraint failed: dummyentity.name"),
    )
    exc.args = ("NOT NULL constraint failed: dummyentity.name",)
    session.exec.side_effect = exc
    monkeypatch.setattr("fed_mgr.v1.crud.split_camel_case", lambda x: "Dummy Entity")

    with pytest.raises(NotNullError) as e:
        update_item(
            entity=DummyEntity, session=session, item_id=item_id, new_data=new_data
        )
    assert "can't be NULL" in str(e.value)
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_update_item_integrity_error_unique(monkeypatch, session):
    """Test update_item raises ConflictError on UNIQUE constraint violation."""
    item_id = uuid.uuid4()
    new_data = MagicMock()
    new_data.model_dump.return_value = {"name": "foo"}

    # Simulate IntegrityError for UNIQUE constraint
    exc = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("UNIQUE constraint failed: dummyentity.name"),
    )
    exc.args = ("UNIQUE constraint failed: dummyentity.name",)
    session.exec.side_effect = exc
    monkeypatch.setattr("fed_mgr.v1.crud.split_camel_case", lambda x: "Dummy Entity")

    with pytest.raises(ConflictError) as e:
        update_item(
            entity=DummyEntity, session=session, item_id=item_id, new_data=new_data
        )
    assert "already exists" in str(e.value)
    session.rollback.assert_called_once()
    session.commit.assert_not_called()


def test_delete_item_executes_and_commits(session):
    """Test delete_item executes the delete statement and commits."""
    item_id = uuid.uuid4()
    delete_item(entity=DummyEntity, session=session, item_id=item_id)
    session.exec.assert_called()
    session.commit.assert_called()
