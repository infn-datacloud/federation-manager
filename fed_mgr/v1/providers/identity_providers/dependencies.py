"""Dependencies for identity provider operations in the federation manager."""

from typing import Annotated

from fastapi import Depends

from fed_mgr.v1.models import ProviderIdPConnection
from fed_mgr.v1.providers.identity_providers.crud import get_prov_idp_link

ProviderIdPConnectionDep = Annotated[
    ProviderIdPConnection | None, Depends(get_prov_idp_link)
]
