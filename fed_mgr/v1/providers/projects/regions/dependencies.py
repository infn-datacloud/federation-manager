"""Dependencies for project configurations in the federation manager."""

from typing import Annotated

from fastapi import Depends

from fed_mgr.v1.models import ProjRegConfig
from fed_mgr.v1.providers.projects.regions.crud import get_project_config

ProjRegConfigDep = Annotated[ProjRegConfig | None, Depends(get_project_config)]
