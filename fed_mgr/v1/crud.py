"""Create Read Update and Delete generic functions."""

import re
import uuid
from typing import Any, TypeVar

import sqlalchemy
import sqlalchemy.exc
from sqlmodel import Session, SQLModel, asc, delete, desc, func, select, update

from fed_mgr.exceptions import (
    ConflictError,
    DatabaseOperationError,
    DeleteFailedError,
    ItemNotFoundError,
)
from fed_mgr.utils import split_camel_case
from fed_mgr.v1.models import User
from fed_mgr.v1.schemas import ItemID

Entity = TypeVar("Entity", bound=ItemID)
CreateModel = TypeVar("CreateModel", bound=SQLModel)
UpdateModel = TypeVar("UpdateModel", bound=SQLModel)


def _sqlite_unique_constr_err(err_msg: str, **kwargs) -> str | None:
    """Return an error message when a unique constraing is violated.

    This problem arises only on create and update operations.

    Search for 'UNIQUE constraint failed: ' string and catch anything till the of line
    Example of exceptions:
    - UNIQUE constraint failed: user.sub, user.issuer
    - UNIQUE constraint failed: project.provider_id

    Returns:
        str | None: the error message or None

    """
    match = re.search(r"(?<=UNIQUE\sconstraint\sfailed:\s).+(?=$)", err_msg)
    if match is not None:
        matches = re.findall(r"(?<=\.)\w*", match.group(0))
        if len(matches) > 0:
            dup_values = []
            for i in matches:
                if i == "provider_id":
                    dup_values.append(f"{i}={kwargs.get('provider').id!s}")
                else:
                    dup_values.append(f"{i}={kwargs.get(i)!s}")
            if len(matches) == 1 and matches[0] == "provider_id":
                dup_values.append("is_root=True")
            return ", ".join(dup_values)


def _sqlite_foreign_key_or_not_null_err(err_msg: str) -> str | None:
    """Return an error message when a foreign key or not null constraint is violated.

    This problem arises when trying to delete an entity that is mandatory for another
    one and can't be deleted on cascade.

    Search for 'FOREIGN KEY constraint failed' or 'NOT NULL constraint failed: ' string.
    Example of exceptions:
    - FOREIGN KEY constraint failed
    - NOT NULL constraint failed: identityprovider.created_by_id

    Returns:
        str | None: the error message or None

    """
    match = re.search(r"(?<=FOREIGN\sKEY\sconstraint\sfailed)(?=$)", err_msg)
    if match is not None:
        return "Pointed by another entity."

    match = re.search(r"(?<=NOT\sNULL\sconstraint\sfailed:\s).+(?=$)", err_msg)
    if match is not None:
        matches = re.findall(r"(?<=\.)\w*", match.group(0))
        if len(matches) > 0:
            return "Pointed by another entity"


def _mysql_duplicate_entry(err_msg: str) -> str | None:
    r"""Return an error message when a unique constraing is violated.

    This problem arises only on create and update operations.

    Search for 'Duplicate entry ' string and catch anything till the of line. Based on
    the violated constraint, the error can refers to a single column or more complex
    rules.

    Example of exceptions:
    - Duplicate entry \'6252bba3-d63a-45f1-9cad-415ec82948ca-https://iam.cloud.infn.it/\'
        for key \'user.unique_sub_issuer_couple\'
    - Duplicate entry \'string-7c4531620ddb4100a7c6cf13078a5a90\' for key
        \'project.unique_projid_provider_couple\'
    - Duplicate entry \'7c4531620ddb4100a7c6cf13078a5a90\' for key
        \'project.ix_unique_provider_root\'
    - Duplicate entry \'https://example.com/\' for key \'identityprovider.endpoint\'
    - Duplicate entry \'string\' for key \'provider.name\'

    Returns:
        str | None: the error message or None

    """
    # Search for 'Duplicate entry ' string and catch anything till the end of line
    match = re.search(r"(?<=Duplicate\sentry\s).+(?=$)", err_msg)
    if match is not None:
        # Duplicate user's sub and issuer
        matches = re.findall(
            r"(?<=')([\w\-]*)(?=-([^\s]*)' for key '\w*\.unique_sub_issuer_couple')",
            match.group(0),
        )
        if len(matches) > 0:
            return f"sub={matches[0][0]!s}, issuer={matches[0][1]!s}"

        # Duplicate project's iaas id on same provider
        matches = re.findall(
            r"(?<=')(.*)(?=-([\w]{32})' for key '\w*\.unique_projid_provider_couple')",
            match.group(0),
        )
        if len(matches) > 0:
            provider_id = uuid.UUID(matches[0][1])
            return f"iaas_project_id={matches[0][0]!s}, provider_id={provider_id!s}"

        # Duplicate root project on same provider
        matches = re.findall(
            r"(?<=')([\w]{32})(?=' for key '\w*\.ix_unique_provider_root')",
            match.group(0),
        )
        if len(matches) > 0:
            return "is_root=True"

        # Duplicate key
        matches = re.findall(r"(?<=')(.*)(?=' for key '(\w*)\.(\w*)')", match.group(0))
        if len(matches) > 0:
            return f"{matches[0][2]}={matches[0][0]!s}"


def _mysql_foreign_key(err_msg: str) -> str | None:
    """Return an error message when a foreign key constraint is violated.

    This problem arises when trying to delete an entity that is mandatory for another
    one and can't be deleted on cascade.

    Search for 'Cannot delete or update a parent row: a foreign key constraint fails'
    string.

    Returns:
        str | None: the error message or None

    """
    target = "Cannot delete or update a parent row: a foreign key constraint fails"
    if target in err_msg:
        return "Pointed by another entity."


def _message_for_conflict(err_msg: str, entity: str, **kwargs) -> str | None:
    """Return an error message when failing to add or update an entry into the DB.

    Returns:
        str | None: the error message or None

    """
    element_str = split_camel_case(entity)

    # SQLITE
    message = _sqlite_unique_constr_err(err_msg, **kwargs)
    if message is not None:
        return f"{element_str} with {message} already exists"

    # MYSQL
    message = _mysql_duplicate_entry(err_msg)
    if message is not None:
        return f"{element_str} with {message} already exists"


def _message_for_delete(err_msg: str, entity: str, **kwargs) -> str | None:
    """Return an error message when failing to delete an entry from DB.

    Returns:
        str | None: the error message or None

    """
    entity_id = kwargs.get("id")
    element_str = split_camel_case(entity)
    base_msg = f"{element_str} with ID '{entity_id!s}' can't be deleted. "

    # SQLITE
    message = _sqlite_foreign_key_or_not_null_err(err_msg)
    if message is not None:
        return base_msg + message

    # MYSQL
    message = _mysql_foreign_key(err_msg)
    if message is not None:
        return base_msg + message


def _handle_special_date_fields(
    entity: type[Entity], k: str, v: Any
) -> sqlalchemy.BinaryExpression | None:
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


def _handle_generic_field(
    entity: type[Entity], k: str, v: Any
) -> sqlalchemy.BinaryExpression | None:
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
    if isinstance(v, uuid.UUID):
        return entity.__table__.c.get(k) == v
    elif isinstance(v, str):
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
    elif isinstance(v, list):
        return entity.__table__.c.get(k).in_(v)
    return None


def _get_conditions(
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
        cond = _handle_special_date_fields(entity, k, v) or _handle_generic_field(
            entity, k, v
        )
        if cond is not None:
            conditions.append(cond)
    return conditions


def get_item(*, entity: type[Entity], session: Session, **kwargs) -> Entity | None:
    """Retrieve a single item by its ID from the database.

    When multiple values are returned from the DB query, only the first one is returned.

    Args:
        entity: The SQLModel entity class to query.
        session: The SQLModel session for database access.
        **kwargs: Additional arguments used to filter entities.

    Returns:
        The first entity instance if found, otherwise None.

    """
    if "item_id" in kwargs.keys():
        kwargs["id"] = kwargs.pop("item_id")

    conditions = []
    for k, v in kwargs.items():
        conditions.append(entity.__table__.c.get(k) == v)

    statement = select(entity).where(sqlalchemy.and_(True, *conditions))
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

    conditions = _get_conditions(entity=entity, **kwargs)

    statement = (
        select(entity)
        .offset(skip)
        .limit(limit)
        .order_by(key)
        .filter(sqlalchemy.and_(True, *conditions))
    )
    items = session.exec(statement).all()

    statement = (
        select(func.count())
        .select_from(entity)
        .filter(sqlalchemy.and_(True, *conditions))
    )
    tot_items = session.exec(statement).first()

    return items, tot_items


def add_item(*, entity: type[Entity], session: Session, **kwargs) -> Entity:
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
        db_item = entity(**kwargs)
        session.add(db_item)
        session.commit()
        return db_item
    except sqlalchemy.exc.IntegrityError as e:
        session.rollback()
        message = _message_for_conflict(e.args[0], entity.__name__, **kwargs)
        if message is None:
            raise DatabaseOperationError(e.args[0]) from e
        raise ConflictError(message) from e


def update_item(
    *, entity: type[Entity], session: Session, updated_by: User, **kwargs
) -> None:
    """Update an existing item in the database with new data.

    Args:
        entity: The SQLModel entity class to update.
        session: The SQLModel session for database access.
        updated_by: The User who issued the operation.
        **kwargs: Pydantic/SQLModel model updated fields and additional keyword
            arguments to pass to the entity constructor.

    Raises:
        NotNullError: If a NOT NULL constraint is violated.
        ConflictError: If a UNIQUE constraint is violated.

    """
    conditions = []
    where_values = ""
    for k, v in kwargs.items():
        if isinstance(v, uuid.UUID):
            where_values += f"{k}={v!s}"
            conditions.append(entity.__table__.c.get(k) == v)

    kwargs["updated_by_id"] = updated_by.id

    try:
        statement = (
            update(entity).where(sqlalchemy.and_(True, *conditions)).values(**kwargs)
        )
        result = session.exec(statement)
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        session.rollback()
        message = _message_for_conflict(e.args[0], entity.__name__, **kwargs)
        if message is None:
            raise DatabaseOperationError(e.args[0]) from e
        raise ConflictError(message) from e

    updated_value = result.first()
    if updated_value is None:
        message = f"{split_camel_case(entity.__name__)} with given attributes does not "
        message += f"exist: {where_values!s}"
        raise ItemNotFoundError(message)


def delete_item(*, entity: type[Entity], session: Session, **kwargs) -> None:
    """Delete an item by its ID from the database.

    Args:
        entity: The SQLModel entity class to delete from.
        session: The SQLModel session for database access.
        **kwargs: Additional arguments used to filter entities.

    Raises:
        DeleteFailedError: If the item with the given ID can't be deleted.

    """
    if "item_id" in kwargs.keys():
        kwargs["id"] = kwargs.pop("item_id")

    conditions = []
    for k, v in kwargs.items():
        conditions.append(entity.__table__.c.get(k) == v)

    statement = delete(entity).where(sqlalchemy.and_(True, *conditions))
    try:
        session.exec(statement)
        session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        session.rollback()
        message = _message_for_delete(e.args[0], entity.__name__, **kwargs)
        if message is None:
            raise DatabaseOperationError(e.args[0]) from e
        raise DeleteFailedError(message) from e
