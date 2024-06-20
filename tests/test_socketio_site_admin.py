import pytest
import socketio
from socketio import ClientNamespace
from socketio.exceptions import ConnectionError

sio = socketio.Client()


class SiteAdminNameSpace(ClientNamespace):
    def on_connect(self):
        print(f"Connection to namespace {self.namespace} established")
        self.emit("list_provider_federation_requests", {"username": ""}, "/site_admin")

    def on_connect_error(self, data):
        print(f"Failed to connect to namespace {self.namespace}", data)

    def on_list_provider_federation_requests(self, data):
        print("message received with ", data)

    def on_disconnect(self):
        print(f"disconnected from namespace {self.namespace}")


sio.register_namespace(SiteAdminNameSpace("/site_admin"))


def test_failed_connection():
    with pytest.raises(ConnectionError):
        sio.connect(
            "http://localhost:5000",
            transports=["websocket", "polling"],
            namespaces="/site_admin",
        )


def test_connection():
    sio.connect(
        "http://localhost:5000",
        transports=["websocket", "polling"],
        namespaces="/site_admin",
    )
    assert sio.connected
    assert "/site_admin" in sio.connection_namespaces
