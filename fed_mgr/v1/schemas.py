"""Common pydantic schemas."""

import math
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi.datastructures import URL
from pydantic import AnyHttpUrl, BeforeValidator, computed_field
from sqlmodel import TIMESTAMP, Field, SQLModel


def isoformat(d: datetime) -> str:
    """Convert a datetime or date object to an ISO 8601 format.

    UTC with millisecond precision.

    Args:
        d (datetime | date): The datetime or date object to format.

    Returns:
        str: The ISO 8601 formatted string representation of the input.

    Raises:
        AttributeError: If the input object does not have an 'astimezone' method.

    """
    return d.astimezone(timezone.utc).isoformat(timespec="milliseconds")


class ItemID(SQLModel):
    """Schema usually returned by POST operation with only the item ID.

    All DB entities must inherit from this entity.
    """

    id: Annotated[
        uuid.UUID,
        Field(
            default_factory=uuid.uuid4,
            description="Item unique ID in the DB",
            primary_key=True,
        ),
    ]


class ItemDescription(SQLModel):
    """Schema for an item description."""

    description: Annotated[str, Field(default="", description="Item decription")]


class DescriptionQuery(SQLModel):
    """Schema for querying by the description."""

    description: Annotated[
        str | None,
        Field(default=None, description="The description must contain this string"),
    ]


class SortQuery(SQLModel):
    """Schema for specifying sorting options in queries."""

    sort: Annotated[
        str,
        Field(
            default="-created_at",
            description="Name of the key to use to sort values. "
            "Prefix the '-' char to the chosen key to use reverse order.",
        ),
    ]


class PaginationQuery(SQLModel):
    """Schema to filter lists in GET operations with multiple items."""

    size: Annotated[int, Field(default=5, ge=1, description="Chunk size.")]
    page: Annotated[
        int, Field(default=1, ge=1, description="Divide the list in chunks")
    ]


class Pagination(SQLModel):
    """With pagination details and total elements count."""

    size: Annotated[int, Field(default=5, ge=1, description="Chunk size.")]
    number: Annotated[
        int, Field(default=1, ge=1, description="Divide the list in chunks")
    ]
    total_elements: Annotated[int, Field(description="Total number of items")]

    @computed_field
    @property
    def total_pages(self) -> int:
        """Return the ceiling value of tot_items/page size.

        If there are no elements, there is still one page but with no items.
        """
        val = math.ceil(self.total_elements / self.size)
        return 1 if val == 0 else val


class PageNavigation(SQLModel):
    """Schema with the navigation links to use to navigate through a paginated list."""

    first: Annotated[AnyHttpUrl, Field(description="Link to the first page")]
    prev: Annotated[
        AnyHttpUrl | None,
        Field(default=None, description="Link to the previous page if available"),
    ]
    next: Annotated[
        AnyHttpUrl | None,
        Field(default=None, description="Link to the next page if available"),
    ]
    last: Annotated[AnyHttpUrl, Field(description="Link to the last page")]


class PaginatedList(SQLModel):
    """Schema with the pagination details and navigation links.

    Objects' lists returned by GET operations MUST inherit from this schema.
    """

    page_number: Annotated[int, Field(exclude=True, description="Current page number")]
    page_size: Annotated[int, Field(exclude=True, description="Current page size")]
    tot_items: Annotated[
        int,
        Field(
            exclude=True, description="Number of total items spread across al the pages"
        ),
    ]
    resource_url: Annotated[
        AnyHttpUrl,
        Field(
            exclude=True,
            description="Current resource URL. It may contain query parameters.",
        ),
    ]

    @computed_field
    @property
    def page(self) -> Pagination:
        """Return the pagination details."""
        return Pagination(
            number=self.page_number, size=self.page_size, total_elements=self.tot_items
        )

    @computed_field
    @property
    def links(self) -> PageNavigation:
        """Build navigation links for paginated API responses.

        Args:
            url: The base URL for navigation links.
            size: The number of items per page.
            curr_page: The current page number.
            tot_pages: The total number of pages available.

        Returns:
            PageNavigation: An object containing first, previous, next, and last page
                links.

        """
        url = URL(str(self.resource_url)).remove_query_params("page")
        first_page = url.include_query_params(page=1)._url
        if self.page_number > 1:
            prev_page = url.include_query_params(page=self.page_number - 1)._url
        else:
            prev_page = None

        if self.page_number < self.page.total_pages:
            next_page = url.include_query_params(page=self.page_number + 1)._url
        else:
            next_page = None
        last_page = url.include_query_params(page=self.page.total_pages)._url

        return PageNavigation(
            first=first_page, prev=prev_page, next=next_page, last=last_page
        )


class CreationTime(SQLModel):
    """Schema for tracking the creation time of an entity."""

    created_at: Annotated[
        datetime,
        Field(
            description="Date time of when the entity has been created",
            default_factory=lambda: datetime.now(timezone.utc),
            sa_type=TIMESTAMP(timezone=True),
        ),
    ]


class CreationTimeQuery(SQLModel):
    """Schema used to define request's body parameters."""

    created_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's creation time must be lower than or equal to this "
            "value",
        ),
    ]
    created_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's creation time must be greater than or equal to this "
            "value",
        ),
    ]


class CreationTimeRead(SQLModel):
    """Schema used to format creation time."""

    created_at: Annotated[
        str,
        Field(
            description="Date time of when the entity has been created in ISO format"
        ),
        BeforeValidator(isoformat),
    ]


class Creator(SQLModel):
    """Schema for tracking the user who created an entity."""

    created_by: Annotated[
        uuid.UUID,
        Field(description="User who created this item.", foreign_key="user.id"),
    ]


class CreatorQuery(SQLModel):
    """Schema for querying by the creator's user ID."""

    created_by: Annotated[
        str | None,
        Field(default=None, description="The creator's ID must contain this string"),
    ]


class CreationRead(CreationTimeRead, Creator):
    """Schema for reading creation time and creator's user ID."""


class CreationQuery(CreationTimeQuery, CreatorQuery):
    """Schema for querying by creation time and creator's user ID."""


class UpdateTime(SQLModel):
    """Schema for tracking the last update time of an entity."""

    updated_at: Annotated[
        datetime,
        Field(
            description="Datetime of when the entity has been updated",
            default_factory=lambda: datetime.now(timezone.utc),
            sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
            sa_type=TIMESTAMP(timezone=True),
        ),
    ]


class UpdateQuery(SQLModel):
    """Schema used to define request's body parameters."""

    updated_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's last update time must be lower than or equal to this "
            "value",
        ),
    ]
    updated_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's last update time must be greater than or equal to this "
            "value",
        ),
    ]


class UpdateTimeRead(SQLModel):
    """Schema used to format creation time."""

    updated_at: Annotated[
        str,
        Field(
            description="Date time of the last change made to the entity in ISO format"
        ),
        BeforeValidator(isoformat),
    ]


class Editor(SQLModel):
    """Schema for tracking the user who last edit an entity."""

    updated_by: Annotated[
        uuid.UUID, Field(description="User who last updated this item.")
    ]


class EditorQuery(SQLModel):
    """Schema for querying by the editor's user ID."""

    updated_by: Annotated[
        str | None,
        Field(default=None, description="The editor's ID must contain this string"),
    ]


class EditableRead(UpdateTimeRead, Editor):
    """Schema for reading update time and editor's user ID."""


class EditableQuery(UpdateQuery, EditorQuery):
    """Schema for querying by update time and editor's user ID."""


class ErrorMessage(SQLModel):
    """Schema returned when raising an HTTP exception such as 404."""

    # title: Annotated[str, Field(description="Error title")]
    detail: Annotated[str, Field(description="Error detailed description")]
