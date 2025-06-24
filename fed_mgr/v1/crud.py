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
    *,
    entity: type[Entity],
    session: Session,
    item: CreateModel | UpdateModel,
    error: Exception,
):
    """Handle and raise specific errors for NOT NULL and UNIQUE constraint violations.

    Args:
        entity: The SQLModel entity class involved in the operation.
        session: The SQLModel session for database access.
        item: The model instance being created or updated.
        error: The exception raised during the database operation.

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
            f"{element_str} with {attr} '{item.model_dump().get(attr)}' already exists"
        ) from error


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
        if k == "created_before":
            conditions.append(entity.__table__.c.get("created_at") <= v)
        elif k == "updated_before":
            conditions.append(entity.__table__.c.get("updated_at") <= v)
        elif k == "created_after":
            conditions.append(entity.__table__.c.get("created_at") >= v)
        elif k == "updated_after":
            conditions.append(entity.__table__.c.get("updated_at") >= v)
        elif isinstance(v, str):
            conditions.append(entity.__table__.c.get(k).icontains(v))
        elif isinstance(v, (int, float)):
            if k.endswith("_lte"):
                k = k[:-4]
                conditions.append(entity.__table__.c.get(k) <= v)
            elif k.endswith("_gte"):
                k = k[:-4]
                conditions.append(entity.__table__.c.get(k) >= v)
            else:
                conditions.append(entity.__table__.c.get(k) == v)
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
        raise_from_integrity_error(entity=entity, session=session, item=item, error=e)


def update_item(
    *,
    entity: type[Entity],
    session: Session,
    item_id: uuid.UUID,
    new_data: UpdateModel,
    **kwargs
) -> None:
    """Update an existing item in the database with new data.

    Args:
        entity: The SQLModel entity class to update.
        session: The SQLModel session for database access.
        item_id: The UUID of the item to update.
        new_data: The Pydantic/SQLModel model instance containing updated fields.
        **kwargs: Additional keyword arguments to pass to the entity constructor.

    Raises:
        NoItemToUpdateError: If no item with the given ID exists in the database.
        NotNullError: If a NOT NULL constraint is violated.
        ConflictError: If a UNIQUE constraint is violated.

    """
    try:
        statement = (
            update(entity)
            .where(entity.id == item_id)
            .values(**new_data.model_dump(), **kwargs)
        )
        result = session.exec(statement)
        if result.rowcount == 0:
            element_str = split_camel_case(entity.__name__)
            raise NoItemToUpdateError(f"{element_str} with ID {item_id} does not exist")
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        raise_from_integrity_error(
            entity=entity, session=session, item=new_data, error=e
        )


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
