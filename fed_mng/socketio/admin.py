from typing import Any, Literal

from socketio import AsyncNamespace

from fed_mng.socketio.utils import validate_auth_on_connect


class AdminNamespace(AsyncNamespace):
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
