"""Dependencies for resource region operations in the federation manager."""

from typing import Annotated

from fastapi import Depends

from fed_mgr.v1.models import Region
from fed_mgr.v1.providers.regions.crud import get_region

RegionDep = Annotated[Region | None, Depends(get_region)]
