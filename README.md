
## Developers

### Testing OPA within container

The containerized instance of OPA needs the policies (`opa/policy.rego`) and the data (`opa/data.json`) used to evaluate the input.

The following docker-compose file:
- copies in the `/fedmgr` folder the `./opa` folder contained in this repository.
- starts opa in server mode
- loads the `fedmgr` package and serves it on `localhost:8181/v1/data/fedmgr`.

```yaml
# compose.yaml
services:
  opa:
    image: openpolicyagent/opa
    ports:
      - 8181:8181
    volumes:
      - ./opa:/fedmgr:ro
    command: run --server --log-level debug /fedmgr
```

```bash
docker compose up -d
```

Once OPA is up and running we can interrogate its endpoints to evaluate the inpute contained in `v1-data-input.json`. Here we give an example of the input to provide to the OPA REST API.

```json
# v1-data-input.json
{
    "input": {
        "authorization": "Bearer <token>"
    }
}
```

```bash
curl localhost:8181/v1/data/fedmgr/user_roles -d @v1-data-input.json -H 'Content-Type: application/json'
```

### Testing SocketIO with python client

In the `examples` folder we provide a python script with a Socket.IO client. It tries to connect to the `/site_admin` namespace and emit a message.

Since endpoints requires a valid token, this example expects the access token as an input to the `--token` (or `-t`) argument. Alternatively you can set the `$SOCKETIO_CLIENT_TOKEN` env var.

```bash
python examples/client.py -t <TOKEN>
```

You can copy and edit that file to make more complexes examples or tests.