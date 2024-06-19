from typing import Literal
from flaat.exceptions import FlaatUnauthenticated
from socketio import AsyncNamespace

from fed_mng.auth import flaat, get_user_roles, is_site_admin


class SiteAdminNamespace(AsyncNamespace):
    async def on_connect(self, sid, environ, auth: dict[Literal["token"], str]):
        """When connecting evaluate user authentication.

        Invoke OPA to check if user is authenticated or not and check it has the
        site_admin role.

        Args:
            sid (_type_): _description_
            environ (_type_): _description_
        """
        print("Connecting to namespace:", self.namespace, sid, environ, auth)
        if auth is None or auth.get("token", None) is None:
            raise ConnectionRefusedError(
                "Authentication failed: No authentication data nor access token received."
            )
        try:
            assert is_site_admin(auth.get("token", "")), ConnectionRefusedError(
                "Authentication failed: User does not have needed access rights."
            )
        except FlaatUnauthenticated as e:
            raise ConnectionRefusedError(e) from e
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
