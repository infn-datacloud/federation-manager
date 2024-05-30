"""SocketIO server."""
import eventlet
import eventlet.wsgi
import socketio

sio = socketio.Server()
app = socketio.WSGIApp(sio)


@sio.event
def connect(sid, environ, auth):
    """When connecting evaluate user authentication.

    Invoke OPA to check if user is authenticated or not and detect its roles.

    Args:
        sid (_type_): _description_
        environ (_type_): _description_
    """
    print("connect ", sid, environ, auth)
    if auth is None:
        raise ConnectionRefusedError(
            "Authentication failed: No authentication data received."
        )
    # TODO: Call OPA to authenticate user


@sio.event(namespace="/site_admin")
def list_provider_federation_requests(sid, data):
    """List submitted requirest.

    Data contains the username or the user email to use to filter on provider federation
    requests.

    Args:
        sid (_type_): _description_
        data (_type_): _description_
    """
    print("Received data ", data)
    # TODO: Retrieve list of federated providers


@sio.event(namespace="/site_admin")
def submit_new_provider_federation_request(sid, data):
    """Submit a new provider federation request.

    Data contains the username or the user email of the issuer and the provider data.

    Args:
        sid (_type_): _description_
        data (_type_): _description_
    """
    print("Received data ", data)
    # TODO: Start a new workflow instance to federate a provider


@sio.event(namespace="/site_admin")
def update_federated_provider(sid, data):
    """Submit a request to update an already federated provider.

    Data contains the updated provider data.

    Args:
        sid (_type_): _description_
        data (_type_): _description_
    """
    print("Received data ", data)
    # TODO: Start a new workflow instance to update a provider


@sio.event(namespace="/site_admin")
def delete_federated_provider(sid, data):
    """Submit a request to delete an already federated provider.

    Data contains the id of the target provider.

    Args:
        sid (_type_): _description_
        data (_type_): _description_
    """
    print("Received data ", data)
    # TODO: Start a new workflow instance to delete a provider


@sio.event
def disconnect(sid):
    """Close connection

    Args:
        sid (_type_): _description_
    """
    print("disconnect ", sid)


if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("", 5000)), app)
