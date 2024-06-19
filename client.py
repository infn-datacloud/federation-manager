import socketio
from socketio import ClientNamespace
from socketio.exceptions import ConnectionError

sio = socketio.Client()


class SiteAdminNameSpace(ClientNamespace):
    def on_connect(self):
        print(f"Connection to namespace {self.namespace} established")
        self.emit("list_provider_federation_requests", {"username": ""}, "/site_admin")

    def on_test(self, data):
        print("received_data", data)

    def on_connect_error(self, data):
        print(f"Failed to connect to namespace {self.namespace}", data)

    def on_list_provider_federation_requests(self, data):
        print("message received with ", data)

    def on_disconnect(self):
        print(f"disconnected from namespace {self.namespace}")


sio.register_namespace(SiteAdminNameSpace("/site_admin"))

sio.connect(
    "http://localhost:8000",
    transports=["websocket", "polling"],
    namespaces="/site_admin",
    #headers={"Autorization": f"Bearer {token}"},
    auth={"token": token},
)
sio.wait()


# from fastapi.testclient import TestClient

# from fed_mng.main3 import app


# def test_websocket():
#     client = TestClient(app)
#     with client.websocket_connect("/site_admin") as websocket:
#         data = websocket.receive_json()
#         assert data == {"msg": "Hello WebSocket"}