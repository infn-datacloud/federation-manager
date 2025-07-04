"""Dependencies for location operations in the federation manager."""

from typing import Annotated

from fastapi import Depends

from fed_mgr.v1.locations.crud import get_location
from fed_mgr.v1.models import Location

LocationDep = Annotated[Location | None, Depends(get_location)]
