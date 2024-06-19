
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
