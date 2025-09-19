"""Regions schemas returned by the endpoints."""

from typing import Annotated

from sqlmodel import Field

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


class RegionBase(ItemDescription):
    """Schema with the basic parameters of the Region entity."""

    name: Annotated[
        str,
        Field(
            default="default",
            description="For resource providers supporting multiple regions this value "
            "must match the resource provider region. Otherwise it is a placeholder.",
        ),
    ]
    overbooking_cpu: Annotated[
        float, Field(default=1, description="Value used to overbook RAM.")
    ]
    overbooking_ram: Annotated[
        float, Field(default=1, description="Value used to overbook CPUs.")
    ]
    bandwidth_in: Annotated[
        float, Field(default=10, description="Input network bandwidth.")
    ]
    bandwidth_out: Annotated[
        float, Field(default=10, description="Output network bandwidth.")
    ]


class RegionCreate(RegionBase):
    """Schema used to create a Region."""

    # location_id: Annotated[
    #     uuid.UUID,
    #     Field(description="ID of the physical site hosting the region's resources."),
    # ]


# class RegionLinks(SQLModel):
#     """Schema containing links related to the Region."""

#     location: Annotated[
#         AnyHttpUrl,
#         Field(
#             description="Link to retrieve the location hosting region's resources."
#         ),
#     ]


class RegionRead(ItemID, CreationRead, EditableRead, RegionBase):
    """Schema used to read an Region."""

    # links: Annotated[
    #     RegionLinks,
    #     Field(
    #         sa_type=AutoString,
    #         description="Dict with the links of the project related entities",
    #     ),
    # ]


class RegionList(PaginatedList):
    """Schema used to return paginated list of Regions' data to clients."""

    data: Annotated[
        list[RegionRead],
        Field(default_factory=list, description="List of resource projects"),
    ]


class RegionQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    name: Annotated[
        str | None,
        Field(default=None, description="Region name must contain this string"),
    ]
    overbooking_cpu_gte: Annotated[
        float | None,
        Field(default=None, description="Overbook RAM must be greater than or equal."),
    ]
    overbooking_cpu_lte: Annotated[
        float | None,
        Field(default=None, description="Overbook RAM must be lower than or equal."),
    ]
    overbooking_ram_gte: Annotated[
        float | None,
        Field(default=None, description="Overbook CPUs must be greater than or equal"),
    ]
    overbooking_ram_lte: Annotated[
        float | None,
        Field(default=None, description="Overbook CPUs must be lower than or equal."),
    ]
    bandwidth_in_gte: Annotated[
        float | None,
        Field(
            default=None,
            description="Input network bandwidth must be greater than or equal.",
        ),
    ]
    bandwidth_in_lte: Annotated[
        float | None,
        Field(
            default=None,
            description="Input network bandwidth must be lower than or equal.",
        ),
    ]
    bandwidth_out_gte: Annotated[
        float | None,
        Field(
            default=None,
            description="Output network bandwidth must be greater than or equal.",
        ),
    ]
    bandwidth_out_lte: Annotated[
        float | None,
        Field(
            default=None,
            description="Output network bandwidth must be lower than or equal.",
        ),
    ]
