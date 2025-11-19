"""Unit tests for v1 common crud functions.

These tests cover:
- raise_from_db_error for NOT NULL, UNIQUE, and generic errors
- get_conditions for string, numeric, and date filters
- get_item for correct session.exec usage
- get_items for correct select/count statements and empty results
- add_item for normal, created_by, NOT NULL, and UNIQUE constraint cases
- update_item for success, no item, NOT NULL, and UNIQUE constraint cases
- delete_item for correct execution and commit
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy
from sqlalchemy.dialects.sqlite import dialect
from sqlmodel import Field, SQLModel

from fed_mgr.exceptions import (
    ConflictError,
    DatabaseOperationError,
    DeleteFailedError,
    ItemNotFoundError,
)
from fed_mgr.v1.crud import (
    _handle_generic_field,
    _handle_special_date_fields,
    add_item,
    delete_item,
    get_item,
    get_items,
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
    age: int = Field(default=0)
    score: float = Field(default=0.0)


def compile_expr(expr):
    """Compile SQLAlchemy expression to SQL string for assertion."""
    return str(expr.compile(dialect=dialect())).lower()


# def test_raise_from_db_error_unique(session):
#     """Test raise_from_db_error raises ConflictError on NOT UNIQUE constraint."""
#     item = MagicMock()
#     item.model_dump.return_value = {"name": "foo"}
#     error = Exception("UNIQUE constraint failed: dummyentity.name")
#     error.args = ("UNIQUE constraint failed: dummyentity.name",)
#     with pytest.raises(ConflictError) as exc:
#         raise_from_db_error(
#             entity=DummyEntity, session=session, error=error, **item.model_dump()
#         )
#     assert "Dummy Entity with name=foo already exists" in str(exc.value)
#     session.rollback.assert_called_once()

#     # TODO case when match starts with index


# def test_raise_from_db_error_other_error(session):
#     """Test raise_from_db_error raises a generic error."""
#     item = MagicMock()
#     item.model_dump.return_value = {"name": "foo"}
#     error = Exception("Some other error")
#     error.args = ("Some other error",)
#     raise_from_db_error(
#         entity=DummyEntity, session=session, error=error, **item.model_dump()
#     )
#     session.rollback.assert_called_once()


def test_get_item_with_id(session):
    """Test get_item correctly filters using id parameter."""
    item_id = uuid.uuid4()
    session.exec.return_value.first.return_value = "test_item"
    result = get_item(entity=DummyEntity, session=session, id=item_id)

    session.exec.assert_called_once()
    first_call_args = session.exec.call_args_list[0][0]
    statement = first_call_args[0]
    assert any("dummyentity.id =" in str(i) for i in statement._where_criteria)

    assert result == "test_item"


def test_get_item_with_item_id(session):
    """Test get_item correctly maps item_id to id parameter."""
    item_id = uuid.uuid4()
    session.exec.return_value.first.return_value = "test_item"
    result = get_item(entity=DummyEntity, session=session, item_id=item_id)

    session.exec.assert_called_once()
    first_call_args = session.exec.call_args_list[0][0]
    statement = first_call_args[0]
    assert any("dummyentity.id =" in str(i) for i in statement._where_criteria)

    assert result == "test_item"


def test_get_item_not_found(session):
    """Test get_item returns None when item is not found."""
    item_id = uuid.uuid4()
    session.exec.return_value.first.return_value = None
    result = get_item(entity=DummyEntity, session=session, id=item_id)

    session.exec.assert_called_once()
    first_call_args = session.exec.call_args_list[0][0]
    statement = first_call_args[0]
    assert any("dummyentity.id =" in str(i) for i in statement._where_criteria)

    assert result is None


def test_get_item_with_multiple_filters(session):
    """Test get_item correctly applies multiple filter conditions."""
    item_id = uuid.uuid4()
    name = "test_name"
    age = 123
    session.exec.return_value.first.return_value = "test_item"

    result = get_item(
        entity=DummyEntity, session=session, id=item_id, name=name, age=age
    )

    session.exec.assert_called_once()
    first_call_args = session.exec.call_args_list[0][0]
    statement = first_call_args[0]
    assert any("dummyentity.id =" in str(i) for i in statement._where_criteria)
    assert any("dummyentity.name =" in str(i) for i in statement._where_criteria)
    assert any("dummyentity.age =" in str(i) for i in statement._where_criteria)

    assert result == "test_item"


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


def test_get_items_with_args(session):
    """Test get_items calls session.exec with correct select statement for items."""
    # Prepare mocks
    session.exec.side_effect = [
        MagicMock(all=lambda: ["item1", "item2"]),
        MagicMock(first=lambda: 2),
    ]
    key = "created_at"
    name = "test_name"
    age = 123

    # Call get_items
    items, tot = get_items(
        entity=DummyEntity,
        session=session,
        skip=5,
        limit=10,
        sort=key,
        name=name,
        age=age,
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
    assert any("created_at" in str(o) for o in statement._order_by_clauses)
    assert any(
        "lower(dummyentity.name) LIKE" in str(i) for i in statement._where_criteria
    )
    assert any("dummyentity.age =" in str(i) for i in statement._where_criteria)

    # Check the second call to session.exec (for count)
    second_call_args = session.exec.call_args_list[1][0]
    count_statement = second_call_args[0]
    # The count statement should not have offset or limit
    assert not getattr(count_statement, "_limit", None)
    assert not getattr(count_statement, "_offset", None)
    assert hasattr(statement, "order_by")
    assert any("created_at" in str(o) for o in statement._order_by_clauses)
    assert any(
        "lower(dummyentity.name) LIKE" in str(i) for i in statement._where_criteria
    )
    assert any("dummyentity.age =" in str(i) for i in statement._where_criteria)

    assert items == ["item1", "item2"]
    assert tot == 2
    assert session.exec.call_count == 2


def test_add_item(session):
    """Test add_item adds the entity to the session and commits."""
    item = MagicMock(spec=DummyEntity)
    item.model_dump.return_value = {"id": uuid.uuid4()}
    result = add_item(
        entity=DummyEntity, session=session, created_by=None, **item.model_dump()
    )
    session.add.assert_called()
    session.commit.assert_called()
    assert isinstance(result, DummyEntity)


def test_add_item_raises_exc(session):
    """Test add_item raises ConflictError on UNIQUE constraint violation."""
    item = MagicMock(spec=DummyEntity)
    item.model_dump.return_value = {"id": uuid.uuid4(), "name": "foo"}

    # Simulate IntegrityError
    session.commit.side_effect = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("Generic error"),
    )

    with patch(
        "fed_mgr.v1.crud._message_for_conflict", return_value="Generic error"
    ) as mock_raise:
        with pytest.raises(ConflictError):
            add_item(
                entity=DummyEntity,
                session=session,
                created_by=None,
                **item.model_dump(),
            )
        mock_raise.assert_called()
    session.rollback.assert_called()

    with patch(
        "fed_mgr.v1.crud._message_for_conflict", return_value=None
    ) as mock_raise:
        with pytest.raises(DatabaseOperationError):
            add_item(
                entity=DummyEntity,
                session=session,
                created_by=None,
                **item.model_dump(),
            )
        mock_raise.assert_called()
    session.rollback.assert_called()


def test_update_item_success(session):
    """Test update_item successfully updates and commits when rowcount > 0."""
    item_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    new_data = MagicMock()
    new_data.model_dump.return_value = {"name": "newname"}

    # Mock session.exec to return an object with rowcount > 0
    exec_result = MagicMock()
    first_result = MagicMock()
    exec_result.first.return_value = first_result
    session.exec.return_value = exec_result

    result = update_item(
        entity=DummyEntity,
        session=session,
        updated_by=user,
        id=item_id,
        **new_data.model_dump(),
    )
    session.exec.assert_called()
    session.commit.assert_called_once()

    assert result is None  # FIXME: result == first_result

    # Check the first call to session.exec
    first_call_args = session.exec.call_args_list[0][0]
    statement = first_call_args[0]
    # The statement should be a select on DummyEntity with correct offset, limit, and
    # order_by
    assert hasattr(statement, "values")
    assert any("dummyentity.id =" in str(i) for i in statement._where_criteria)
    assert any("dummyentity.id" in str(i) for i in statement._values)
    assert any("dummyentity.name" in str(i) for i in statement._values)
    assert any("updated_by_id" in str(i) for i in statement._values)
    assert statement._returning is not None


def test_update_item_no_item_to_update(session):
    """Test update_item raises ItemNotFoundError when rowcount == 0."""
    item_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    new_data = MagicMock()
    new_data.model_dump.return_value = {"name": "newname"}

    # Mock session.exec to return an object with rowcount = 0
    exec_result = MagicMock()
    exec_result.first.return_value = None
    session.exec.return_value = exec_result

    with pytest.raises(
        ItemNotFoundError,
        match=f"Dummy Entity with given attributes does not exist: id={item_id!s}",
    ):
        update_item(
            entity=DummyEntity,
            session=session,
            updated_by=user,
            id=item_id,
            **new_data.model_dump(),
        )
    session.exec.assert_called()
    session.commit.assert_called()


def test_update_item_integrity_error(session):
    """Test update_item raises ConflictError on UNIQUE constraint violation."""
    item_id = uuid.uuid4()
    user = MagicMock()
    user.id = uuid.uuid4()
    new_data = MagicMock()
    new_data.model_dump.return_value = {"name": "foo"}

    # Simulate IntegrityError for UNIQUE constraint
    exc = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("Generic error"),
    )
    session.exec.side_effect = exc

    with patch(
        "fed_mgr.v1.crud._message_for_conflict", return_value="Generic error"
    ) as mock_raise:
        with pytest.raises(ConflictError):
            update_item(
                entity=DummyEntity,
                session=session,
                updated_by=user,
                id=item_id,
                **new_data.model_dump(),
            )
        mock_raise.assert_called_once()
    session.exec.assert_called()
    session.rollback.assert_called()
    session.commit.assert_not_called()

    with patch(
        "fed_mgr.v1.crud._message_for_conflict", return_value=None
    ) as mock_raise:
        with pytest.raises(DatabaseOperationError):
            update_item(
                entity=DummyEntity,
                session=session,
                updated_by=user,
                id=item_id,
                **new_data.model_dump(),
            )
        mock_raise.assert_called_once()
    session.exec.assert_called()
    session.rollback.assert_called()
    session.commit.assert_not_called()


def test_delete_item_success(session):
    """Test delete_item executes the delete statement and commits."""
    item_id = uuid.uuid4()
    delete_item(entity=DummyEntity, session=session, id=item_id)
    session.exec.assert_called()
    session.commit.assert_called()

    # Check the first call to session.exec
    first_call_args = session.exec.call_args_list[0][0]
    statement = first_call_args[0]
    # The statement should be a select on DummyEntity with correct offset, limit, and
    # order_by
    assert any("dummyentity.id =" in str(i) for i in statement._where_criteria)
    assert statement._returning is not None


def test_delete_item_fails(session):
    """Test delete_item executes the delete statement and commits."""
    item_id = uuid.uuid4()

    # Simulate IntegrityError for FOREIGN KEY constraint
    exc = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("Generic error"),
    )
    session.exec.side_effect = exc

    with patch(
        "fed_mgr.v1.crud._message_for_delete", return_value="Generic error"
    ) as mock_raise:
        with pytest.raises(DeleteFailedError):
            delete_item(entity=DummyEntity, session=session, id=item_id)
        mock_raise.assert_called()
    session.exec.assert_called()
    session.rollback.assert_called()
    session.commit.assert_not_called()

    with patch(
        "fed_mgr.v1.crud._message_for_delete", return_value="Generic error"
    ) as mock_raise:
        with pytest.raises(DeleteFailedError):
            delete_item(entity=DummyEntity, session=session, id=item_id)
        mock_raise.assert_called()
    session.exec.assert_called()
    session.rollback.assert_called()
    session.commit.assert_not_called()


def test_uuid_equality():
    """UUID input should produce an equality filter."""
    uid = uuid.uuid4()
    expr = _handle_generic_field(DummyEntity, "id", uid)
    sql = compile_expr(expr)
    assert "id =" in sql


def test_string_icontains():
    """String input should produce an icontains LIKE filter."""
    expr = _handle_generic_field(DummyEntity, "name", "abc")
    sql = compile_expr(expr)
    # using ILIKE/LIKE depending on backend, so check for LIKE pattern
    assert "like" in sql


def test_numeric_equality():
    """Numeric input without suffix should produce equality filter."""
    expr = _handle_generic_field(DummyEntity, "age", 30)
    sql = compile_expr(expr)
    assert "age =" in sql


def test_numeric_lte():
    """_lte suffix should produce <= filter."""
    expr = _handle_generic_field(DummyEntity, "score_lte", 50.5)
    sql = compile_expr(expr)
    assert "score <=" in sql


def test_numeric_gte():
    """_gte suffix should produce >= filter."""
    expr = _handle_generic_field(DummyEntity, "score_gte", 10)
    sql = compile_expr(expr)
    assert "score >=" in sql


def test_list_in_operator():
    """List value should produce an IN clause."""
    expr = _handle_generic_field(DummyEntity, "age", [1, 2, 3])
    sql = compile_expr(expr)
    assert "age in" in sql


def test_unsupported_type_returns_none():
    """Unsupported types should return None."""

    class X:
        pass

    assert _handle_generic_field(DummyEntity, "name", X()) is None


def test_created_before():
    """created_before should produce created_at <= v."""
    dt = datetime(2024, 1, 1)
    expr = _handle_special_date_fields(DummyEntity, "created_before", dt)
    sql = compile_expr(expr)
    assert "created_at <=" in sql


def test_created_after():
    """created_after should produce created_at >= v."""
    dt = datetime(2024, 1, 2)
    expr = _handle_special_date_fields(DummyEntity, "created_after", dt)
    sql = compile_expr(expr)
    assert "created_at >=" in sql


def test_updated_before():
    """updated_before should produce updated_at <= v."""
    dt = datetime(2024, 2, 1)
    expr = _handle_special_date_fields(DummyEntity, "updated_before", dt)
    sql = compile_expr(expr)
    assert "updated_at <=" in sql


def test_updated_after():
    """updated_after should produce updated_at >= v."""
    dt = datetime(2024, 2, 2)
    expr = _handle_special_date_fields(DummyEntity, "updated_after", dt)
    sql = compile_expr(expr)
    assert "updated_at >=" in sql


def test_start_before():
    """start_before should produce start_date <= v."""
    dt = datetime(2024, 3, 1)
    expr = _handle_special_date_fields(DummyEntity, "start_before", dt)
    sql = compile_expr(expr)
    assert "start_date <=" in sql


def test_start_after():
    """start_after should produce start_date >= v."""
    dt = datetime(2024, 3, 2)
    expr = _handle_special_date_fields(DummyEntity, "start_after", dt)
    sql = compile_expr(expr)
    assert "start_date >=" in sql


def test_end_before():
    """end_before should produce end_date <= v."""
    dt = datetime(2024, 4, 1)
    expr = _handle_special_date_fields(DummyEntity, "end_before", dt)
    sql = compile_expr(expr)
    assert "end_date <=" in sql


def test_end_after():
    """end_after should produce end_date >= v."""
    dt = datetime(2024, 4, 2)
    expr = _handle_special_date_fields(DummyEntity, "end_after", dt)
    sql = compile_expr(expr)
    assert "end_date >=" in sql


def test_unsupported_key_returns_none():
    """Unsupported key should return None."""
    assert _handle_special_date_fields(DummyEntity, "not_a_key", datetime.now()) is None
