# Testing OPA within container

The containerized instance of OPA needs the policies (`opa/example-policy.rego`) and the data (`opa/example-data.json`) used to evaluate the input.

The following docker-compose file:
- copies in the `/fed-mgr` folder the `../opa/data` folder contained in this repository.
- starts opa in server mode
- loads the `fed-mgr` package and serves it on `localhost:8181/v1/data/fed-mgr`.

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

The expected result should be: `{"result":true}`
