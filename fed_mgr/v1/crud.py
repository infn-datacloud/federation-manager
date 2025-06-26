"""Create Read Update and Delete generic functions."""

import re
import uuid
from typing import TypeVar

import sqlalchemy
from sqlmodel import Session, SQLModel, asc, delete, desc, func, select, update

from fed_mgr.exceptions import ConflictError, NoItemToUpdateError, NotNullError
from fed_mgr.utils import split_camel_case
from fed_mgr.v1.schemas import ItemID

Entity = TypeVar("Entity", bound=ItemID)
CreateModel = TypeVar("CreateModel", bound=SQLModel)
UpdateModel = TypeVar("UpdateModel", bound=SQLModel)


def raise_from_integrity_error(
    *, entity: type[Entity], session: Session, error: Exception, **kwargs
):
    """Handle and raise specific errors for NOT NULL and UNIQUE constraint violations.

    Args:
        entity: The SQLModel entity class involved in the operation.
        session: The SQLModel session for database access.
        error: The exception raised during the database operation.
        kwargs: The received model attributes.

    Raises:
        NotNullError: If a NOT NULL constraint is violated.
        ConflictError: If a UNIQUE constraint is violated.

    """
    session.rollback()
    element_str = split_camel_case(entity.__name__)

    match = re.search(r"(?<=NOT\sNULL\sconstraint\sfailed:\s).*", error.args[0])
    if match is not None:
        attr = match.group(0).split(".")[1]
        raise NotNullError(
            f"Attribute '{attr}' of {element_str} can't be NULL"
        ) from error

    match = re.search(r"(?<=UNIQUE\sconstraint\sfailed:\s).*", error.args[0])
    if match is not None:
        attr = match.group(0).split(".")[1]
        raise ConflictError(
            f"{element_str} with {attr} '{kwargs.get(attr)}' already exists"
        ) from error


def _handle_special_date_fields(entity, k, v):
    """Handle special date field filters for SQLAlchemy queries.

    Given an entity, a key, and a value, this function checks if the key corresponds
    to a special date filter (such as 'created_before', 'updated_after', etc.).
    If so, it returns a SQLAlchemy binary expression suitable for filtering the entity
    based on the specified date field and comparison operator. If the key does not
    match any special date filter, returns None.

    Args:
        entity: The SQLAlchemy model or table to filter.
        k (str): The filter key indicating the date field and comparison
            (e.g., 'created_before').
        v: The value to compare the date field against.

    Returns:
        A SQLAlchemy binary expression for filtering, or None if the key is not a
        special date filter.

    """
    field_map = {
        "created_before": ("created_at", "<="),
        "created_after": ("created_at", ">="),
        "updated_before": ("updated_at", "<="),
        "updated_after": ("updated_at", ">="),
        "start_before": ("start_date", "<="),
        "start_after": ("start_date", ">="),
        "end_before": ("end_date", "<="),
        "end_after": ("end_date", ">="),
    }
    if k in field_map:
        field, op = field_map[k]
        col = entity.__table__.c.get(field)
        if op == "<=":
            return col <= v
        else:
            return col >= v
    return None


def _handle_generic_field(entity, k, v):
    """Handle the creation of SQLAlchemy filter expressions for a given entity's field.

    Args:
        entity: The SQLAlchemy model class or instance whose table columns are being
            filtered.
        k (str): The field name or filter key. For numeric values, may end with '_lte'
            or '_gte' to indicate range filters.
        v (str, int, float): The value to filter by. Strings are used for
            case-insensitive containment; numbers for equality or range.

    Returns:
        sqlalchemy.sql.elements.BinaryExpression corresponding to the field and value,
        or None if the value type is unsupported.

    Notes:
        - For string values, performs a case-insensitive containment filter (LIKE '%v%')
        - For numeric values, supports less-than-or-equal ('_lte'),
        greater-than-or-equal ('_gte'), and equality filters.

    """
    if isinstance(v, str):
        return entity.__table__.c.get(k).icontains(v)
    elif isinstance(v, (int, float)):
        if k.endswith("_lte"):
            k = k[:-4]
            return entity.__table__.c.get(k) <= v
        elif k.endswith("_gte"):
            k = k[:-4]
            return entity.__table__.c.get(k) >= v
        else:
            return entity.__table__.c.get(k) == v
    return None


def get_conditions(
    *, entity: type[Entity], **kwargs
) -> list[sqlalchemy.BinaryExpression]:
    """Build a list of SQLAlchemy filter conditions for querying items.

    Args:
        entity: The SQLModel entity class to filter.
        **kwargs: Arbitrary filter parameters, such as field values or range conditions.
            Recognized keys include 'created_before', 'created_after', 'updated_before',
            'updated_after', and any field name (with optional _lte/_gte suffix for
            range).

    Returns:
        List of SQLAlchemy binary expressions to be used in a query filter.

    """
    conditions = []
    for k, v in kwargs.items():
        cond = _handle_special_date_fields(entity, k, v)
        if cond is not None:
            conditions.append(cond)
        cond = _handle_generic_field(entity, k, v)
        if cond is not None:
            conditions.append(cond)
    return conditions


def get_item(
    *, entity: type[Entity], session: Session, item_id: uuid.UUID
) -> Entity | None:
    """Retrieve a single item by its ID from the database.

    Args:
        entity: The SQLModel entity class to query.
        session: The SQLModel session for database access.
        item_id: The UUID of the item to retrieve.

    Returns:
        The entity instance if found, otherwise None.

    """
    statement = select(entity).where(entity.id == item_id)
    return session.exec(statement).first()


def get_items(
    *,
    entity: type[Entity],
    session: Session,
    skip: int,
    limit: int,
    sort: str,
    **kwargs,
) -> tuple[list[Entity], int]:
    """Retrieve a paginated and sorted list of items, with total count, from the DB.

    The total count corresponds to the total count of returned values which may differs
    from the showed users since they are paginated.

    Args:
        entity: The SQLModel entity class to query.
        session: The SQLModel session for database access.
        skip: Number of items to skip (for pagination).
        limit: Maximum number of items to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters (see get_conditions).

    Returns:
        Tuple of (list of entity instances, total count of matching items).

    """
    if sort.startswith("-"):
        key = desc(entity.__table__.c.get(sort[1:]))
    else:
        key = asc(entity.__table__.c.get(sort))

    conditions = get_conditions(entity=entity, **kwargs)

    statement = (
        select(entity)
        .offset(skip)
        .limit(limit)
        .order_by(key)
        .filter(sqlalchemy.and_(True, *conditions))
    )
    items = session.exec(statement).all()

    statement = select(func.count(entity.id)).filter(sqlalchemy.and_(True, *conditions))
    tot_items = session.exec(statement).first()

    return items, tot_items


def add_item(
    *, entity: type[Entity], session: Session, item: CreateModel, **kwargs
) -> Entity:
    """Add a new item to the database.

    Args:
        entity: The SQLModel entity class to add.
        session: The SQLModel session for database access.
        item: The Pydantic/SQLModel model instance to add.
        **kwargs: Additional keyword arguments to pass to the entity constructor.

    Returns:
        The newly created entity instance.

    Raises:
        NotNullError: If a NOT NULL constraint is violated.
        ConflictError: If a UNIQUE constraint is violated.

    """
    try:
        db_item = entity(**item.model_dump(), **kwargs)
        session.add(db_item)
        session.commit()
        return db_item
    except sqlalchemy.exc.IntegrityError as e:
        raise_from_integrity_error(
            entity=entity, session=session, error=e, **item.model_dump()
        )


def update_item(
    *, entity: type[Entity], session: Session, item_id: uuid.UUID, **kwargs
) -> None:
    """Update an existing item in the database with new data.

    Args:
        entity: The SQLModel entity class to update.
        session: The SQLModel session for database access.
        item_id: The UUID of the item to update.
        **kwargs: Pydantic/SQLModel model updated fields and additional keyword
            arguments to pass to the entity constructor.

    Raises:
        NoItemToUpdateError: If no item with the given ID exists in the database.
        NotNullError: If a NOT NULL constraint is violated.
        ConflictError: If a UNIQUE constraint is violated.

    """
    try:
        statement = update(entity).where(entity.id == item_id).values(**kwargs)
        result = session.exec(statement)
        if result.rowcount == 0:
            element_str = split_camel_case(entity.__name__)
            raise NoItemToUpdateError(f"{element_str} with ID {item_id} does not exist")
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise_from_integrity_error(entity=entity, session=session, error=e, **kwargs)


def delete_item(*, entity: type[Entity], session: Session, item_id: uuid.UUID) -> None:
    """Delete an item by its ID from the database.

    Args:
        entity: The SQLModel entity class to delete from.
        session: The SQLModel session for database access.
        item_id: The UUID of the item to delete.

    """
    statement = delete(entity).where(entity.id == item_id)
    session.exec(statement)
    session.commit()
