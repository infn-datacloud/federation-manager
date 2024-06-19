from typing import Any, Literal

from socketio import AsyncNamespace

from fed_mng.socketio.utils import validate_auth_on_connect


class SiteAdminNamespace(AsyncNamespace):
    async def on_connect(self, sid: str, environ: dict[str, Any], auth: dict[Literal["token"], str]):
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
