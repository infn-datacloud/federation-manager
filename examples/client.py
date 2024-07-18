import argparse
import os

import socketio
from socketio import ClientNamespace

parser = argparse.ArgumentParser(description="Pass token.")
parser.add_argument(
    "--token",
    "-t",
    type=str,
    default=os.environ.get("SOCKETIO_CLIENT_TOKEN", None),
    help="Access token to use. If not set use the value in the SOCKETIO_CLIENT_TOKEN",
)

args = parser.parse_args()


class SiteAdminNameSpace(ClientNamespace):
    def on_connect(self):
        print(f"Connection to namespace {self.namespace} established")
        self.emit("list_provider_federation_requests", {"username": ""})
        self.emit("get_form")

    def on_connect_error(self, data):
        print(f"Failed to connect to namespace {self.namespace}", data)

    def on_list_provider_federation_requests(self, data):
        print(f"Message received with {data}")

    def on_get_form(self, data):
        print(f"Message received with {data}")

    def on_disconnect(self):
        print(f"Disconnected from namespace {self.namespace}")


sio = socketio.Client()
sio.register_namespace(SiteAdminNameSpace("/site_admin"))


sio.connect(
    "http://localhost:8000",
    transports=["websocket", "polling"],
    auth={"token": args.token},
)
sio.sleep(5)
sio.disconnect()
