"""SocketIO server."""
import eventlet
import eventlet.wsgi
import socketio

from fed_mng.site_admin import SiteAdminNamespace

sio = socketio.Server()
sio.register_namespace(SiteAdminNamespace("/site_admin"))
app = socketio.WSGIApp(sio)


if __name__ == "__main__":
    eventlet.wsgi.server(eventlet.listen(("", 5000)), app)
