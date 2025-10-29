# Run OPA

If you want to test the communication with OPA, you can use the [opa](https://hub.docker.com/r/openpolicyagent/opa) docker image. The containerized instance of OPA needs the policies (`opa/policy.rego`) and the data (`opa/data.json`) used to evaluate the input.

The following command:
- copies in the `/fedmgr` folder the `./opa/data` folder contained in this repository.
- starts opa in server mode
- loads the `fedmgr` package and serves it on `localhost:8181/v1/data/fedmgr`.

```bash
docker run -p 8181:8181 --v ./opa/data:/fedmgr:ro openpolicyagent/opa run --server --log-level debug /fedmgr
```

Once OPA is up and running we can interrogate its endpoints to evaluate if a token has the correct access rights.

Here we give an example of the input to provide to the OPA REST API.

```bash
curl -X POST http://localhost:8181/v1/data/fed-mgr/allow \
-H 'Content-Type: application/javascript' \
-d '{
  "input": {
    "user_info": {
      "iss": "https://iam.cloud.infn.it/",
      "groups": ["admin_role"]
    },   
    "path": "/api/v1/users",
    "method": "GET",
    "has_body": "false"
  }
}'
```

The expected result should be: `{"result":true}`.
