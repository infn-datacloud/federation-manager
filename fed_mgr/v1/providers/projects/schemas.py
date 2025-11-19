"""Projects schemas returned by the endpoints."""

import urllib.parse
import uuid
from typing import Annotated

from pydantic import AfterValidator, AnyHttpUrl, computed_field
from sqlmodel import Field, SQLModel

from fed_mgr.v1 import REGIONS_PREFIX
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemDescription,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


def check_not_empty_string(value: str) -> str:
    """Check input value is not an empty string.

    Args:
        value (str): input string

    Returns:
        str: the same string

    Raises:
        ValueError when len is 0.

    """
    if len(value) == 0:
        raise ValueError("Input value can't be empty string")
    return value


class ProjectBase(ItemDescription):
    """Schema with the basic parameters of the Project entity."""

    name: Annotated[str, Field(description="Friendly name of the resource project")]
    iaas_project_id: Annotated[
        str,
        Field(
            description="Tenant/Namespace/Project ID in the IaaS (resource provider)."
        ),
        AfterValidator(check_not_empty_string),
    ]
    is_root: Annotated[
        bool,
        Field(
            default=False,
            description="Define if the project it the IaaS root project. "
            "Used to perform federation tests.",
        ),
    ]


class ProjectCreate(ProjectBase):
    """Schema used to create a Project."""


class ProjectLinks(SQLModel):
    """Schema containing links related to the Project."""

    regions: Annotated[
        AnyHttpUrl,
        Field(description="Link to retrieve the region's specific configuration."),
    ]


class ProjectRead(ItemID, CreationRead, EditableRead, ProjectBase):
    """Schema used to read an Project."""

    sla: Annotated[
        uuid.UUID | None,
        Field(default=None, description="ID of the SLA assigned to this project"),
    ]
    base_url: Annotated[
        AnyHttpUrl, Field(exclude=True, description="Base URL for the children URL")
    ]

    @computed_field
    @property
    def links(self) -> ProjectLinks:
        """Build the slas endpoints in the ProjectLinks object.

        Returns:
            ProjectLinks: An object with the user_groups attribute.

        """
        link = urllib.parse.urljoin(str(self.base_url), f"{self.id}{REGIONS_PREFIX}")
        return ProjectLinks(regions=link)


class ProjectList(PaginatedList):
    """Schema used to return paginated list of Projects' data to clients."""

    data: Annotated[
        list[ProjectRead],
        Field(default_factory=list, description="List of resource projects"),
    ]


class ProjectQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    name: Annotated[
        str | None,
        Field(
            default=None, description="Resource project name must contain this string"
        ),
    ]
    iaas_project_id: Annotated[
        str | None,
        Field(
            default=None,
            description="Tenant/Namespace/Project ID in the IaaS (resource provider) "
            "must contain this string",
        ),
    ]
    is_root: Annotated[
        bool | None,
        Field(default=None, description="The project must be or not be root"),
    ]
    sla: Annotated[
        uuid.UUID | None,
        Field(default=None, description="The SLA's ID must contain this string"),
    ]
