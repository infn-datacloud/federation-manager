from typing import Any, Literal

import requests
from socketio import AsyncNamespace

from fed_mng.config import get_settings
from fed_mng.socketio.utils import validate_auth_on_connect


class SiteAdminNamespace(AsyncNamespace):
    async def on_connect(
        self, sid: str, environ: dict[str, Any], auth: dict[Literal["token"], str]
    ):
        """When connecting evaluate user authentication."""
        print(f"Connecting to namespace: {self.namespace}")
        print(f"SID: {sid}")
        print(f"Environment variables: {environ}")
        print(f"Auth data: {auth}")
        validate_auth_on_connect(auth=auth, target_role=self.namespace[1:])
        print(f"Connected to namespace '{self.namespace}' with sid '{sid}'")

    async def on_disconnect(self, sid):
        """Close connection

        Args:
            sid (_type_): _description_
        """
        print("disconnect from namespace:", self.namespace, sid)

    async def on_list_provider_federation_requests(self, sid, data):
        """List submitted requirest.

        Data contains the username or the user email to use to filter on provider
        federation requests.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        print("Received data ", data)
        await self.emit("list_provider_federation_requests", {"requests": [1]})
        # TODO: Retrieve list of federated providers

    async def on_submit_new_provider_federation_request(self, sid, data):
        """Submit a new provider federation request.

        Data contains the username or the user email of the issuer and the provider
        data.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        print("Received data ", data)
        # TODO: Start a new workflow instance to federate a provider

    async def on_update_federated_provider(self, sid, data):
        """Submit a request to update an already federated provider.

        Data contains the updated provider data.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        print("Received data ", data)
        # TODO: Start a new workflow instance to update a provider

    async def on_delete_federated_provider(self, sid, data):
        """Submit a request to delete an already federated provider.

        Data contains the id of the target provider.

        Args:
            sid (_type_): _description_
            data (_type_): _description_
        """
        print("Received data ", data)
        # TODO: Start a new workflow instance to delete a provider

    async def on_get_form(self, id):
        """Send a dict with the details to use to submit a new provider request."""
        settings = get_settings()
        resp = requests.get(settings.NEW_PROV_FORM_JSON_SCHEMA_URL)
        idp_data = self._resolve_defs(
            resp.json()["properties"].pop("trusted_idps"), resp.json()["$defs"]
        )
        print("Identity provider section: %r" % idp_data)
        provider_data = self._resolve_defs(
            resp.json()["properties"]["openstack"], resp.json()["$defs"]
        )
        print("Provider section: %r" % provider_data)
        await self.emit("get_form", {"idp": idp_data, "provider": provider_data})

    def _resolve_defs(
        self, data: dict[str, Any], definitions: dict[str, dict]
    ) -> dict[str, dict]:
        """Convert the json schema in a more suitable dict.

        Expand $ref keys with the corresponding definitions.
        Move the required key inside the corresponding dict.

        Return the resolved dict.
        """
        resolved_data = {}

        # Expand references
        for key, value in data.items():
            if isinstance(value, dict):
                value = definitions.get(key) if value.get("$ref", None) else value
                resolved_data[key] = self._resolve_defs(value, definitions)
            else:
                resolved_data[key] = value

        # Add required flag to target item
        required_keys = resolved_data.pop("required", None)
        if required_keys is not None and isinstance(required_keys, list):
            for k in required_keys:
                resolved_data["properties"][k]["required"] = True

        return resolved_data
