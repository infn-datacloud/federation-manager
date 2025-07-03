"""Dependencies for SLA operations in the slas module."""

from typing import Annotated

from fastapi import Depends

from fed_mgr.v1.identity_providers.user_groups.slas.crud import get_sla
from fed_mgr.v1.models import SLA

SLADep = Annotated[SLA | None, Depends(get_sla)]
