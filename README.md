# Federation-Manager

The Federation-Manager is a REST API, written in python, used to manage:
- the federation procedure of new resource providers
- the on-boarding procedure of new scientific communities

The REST API is built using the [FastAPI](https://fastapi.tiangolo.com/) library. 
The application supports authentication through the [flaat](https://flaat.readthedocs.io/en/latest/) library and authorization can be implemented using [OPA](https://www.openpolicyagent.org/).

The application stores its data in a DB and uses the [SQLModel](https://sqlmodel.tiangolo.com/) library (which is based on [SQLAlchemy](https://www.sqlalchemy.org/)) as an abstraction layer for python to communicate with any kind of relational DB. DB migrations are managed using the [alembic](https://alembic.sqlalchemy.org/en/latest/) library.

The application is also designed to communicate with [Kafka](https://kafka.apache.org/) to read the monitoring results on the federated resource providers.

A docker image for this service is available on both docker-hub [indigopaas/fed-mgr](https://hub.docker.com/r/indigopaas/fed-mgr) and on INFN Cloud's harbor [harbor.cloud.infn.it/datacloud-middleware/fed-mgr](https://harbor.cloud.infn.it/harbor/projects/19/repositories/fed-mgr/info-tab).

## Run the application

### Local mode

Requirements:
- python >= 3.12
- [poetry](https://python-poetry.org/) >= 2.1

If you want to run the application directly on your host, you must at first configure your environment. These steps must be executed only the first time you clone this repository:

- Install the needed python packages using poetry
  
  ```bash
  poetry install --without dev --with rest-api
  ```

  This command will install the required python packages to run the REST API and will excludes the packages needed for app development. It generates a `.venv` directory in your workspace directory (not tracked by git). 
  
  If you are willing to use a MySQL DB add the `--with mysql` option. By default, it will use a in-memory SQLite DB.

- Activate the generated virtualenv

  ```bash
  poetry env activate 
  ```

- Create a `.env` file and add to it the required environment variables. You can rename the `.env.example` file and change it for your needs. 

  For a list of available environment variables see the [Environment variables](#environment-variables) section.

Once your environment has been correctly configured you can start the application.

```bash
fastapi run fed_mgr/main.py
```

The service will start and listen for requests on port 8000 of your host. If you want to change the port set it using `--port <PORT>` argument.

### Container mode

Requirements:
- [docker](https://www.docker.com/)
- [docker-compose](https://docs.docker.com/compose/) (if you want to run the compose already available on this repository)

Run the docker image (if the image is not available it will be automatically downloaded from the docker reporitory):

```bash
docker run -p 8000:80 --env SECRET_KEY=<MY_SECRET> harbor.cloud.infn.it/datacloud-middleware/fed-mgr 
```

This command starts the application on port 8000 of your host and set the SECRET_KEY environment variable (which is mandatory).
If you want to pass multiple environment variables you can do so passing the file name to the `--env-file` argument.

> Container's user is a non-root user.

> On start up, the application updates the target DB to match the latest DB models.

As an alternative, you can use the example docker compose file available in this repository:

```bash
docker compose -f docker/compose.yaml up -d
```

This commands starts in detached mode the following containers:
- A MySQL DB with a dedicated volume for its data.
- An OPA instance bound to the `opa/data` directory which contains the data and policies to use to authorize requests.
- A fed-mgr REST API instance bound to the `certs` directory which can store the certificates used to communicate with kafka.

## Configuring the communication with Kafka

_If you want to test the integration with Kafka you need a running kafka instance._ If you don't have one, see the [Run OPA](#run-opa) section.

Once you have set up your OPA instance, set `AUTHZ_MODE=opa` and set `OPA_AUTHZ_URL` to point to the OPA server endpoint with the Federation-Manager specific rules.

## Configuring OPA rules for authorization

_If you want to test the integration with OPA you need a running OPA server instance._ If you don't have one, see the [Run Kafka](#run-kafka) section.

Once you have set up your kafka instance, set `KAFKA_ENABLE=true` and verify that the following environment variables as correctly set: `KAFKA_BOOTSTRAP_SERVERS` and `KAFKA_RALLY_RESULTS_TOPIC`.

If you kafka instance has SSL communication enabled, copy in the certs folder of the projects the CA, the CERT and the KEY files to use; then set `KAFKA_SSL_ENABLE=true` and correctly set the `KAFKA_SSL_CACERT_PATH`, `KAFKA_SSL_CERT_PATH` and `KAFKA_SSL_KEY_PATH` environment variables to point to the corresponding files. If the certificate is encrypted provide the password used to encrypt it in the `KAFKA_SSL_PASSWORD` enviroment variable.

## Environment variables

| Name | Type | Required | Default | Description |
|-|-|-|-|-|
| PROJECT_NAME | str | No | Federation-Manager | Project name to show in the Swagger documentation |
| MAINTAINER_NAME | str | No | None | Maintainer name |
| MAINTAINER_URL | str (URI format) | No | None | Maintainer's profile URL |
| MAINTAINER_EMAIL | str (Email format) | No | None | Maintainer's email address |
| LOG_LEVEL | str | No | INFO | Logs level. One between: _CRITICAL_, _ERROR_, _WARNING_, _INFO_ or _DEBUG_ |
| BASE_URL | str (URI format) | No | http://localhost:8000 | Application base URL. Used to build documentation redirect links |
| BACKEND_CORS_ORIGINS | list of str (URI format) | No | [http://localhost:3000/] | JSON-formatted list of allowed origins",
| SECRET_KEY | str | Yes | None | Secret key used to encrypt values in the DB. **To generate a valid key run the following command in shell and copy the generated output: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`** |
| DB_URL | str | No | sqlite+pysqlite:///:memory: | DB URL. By default it use an in memory SQLite DB. The application builds the DB URL starting from `DB_SCHEME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` and `DB_NAME` environment variables only if **all** of them have been defined. If `DB_URL` has been set to None and not all of these variables have been defined, DB URL can't be defined and the application can't start. |
| DB_SCHEME | str | No | None | Database type and library (i.e _mysql+pymysql_) |
| DB_USER | str | No | None | Database user |
| DB_PASSWORD | str | No | None | Database user password |
| DB_HOST | str | No | None | Database hostname |
| DB_PORT | int | No | None | Database exposed port |
| DB_NAME | str | No | None | Name of the database's schema to use |
| DB_ECO | bool | No | False | Print DB operations |
| AUTHN_MODE | str | Yes | None | Authentication method to use. Allowed values: _local_ (uses flaat module) |
| AUTHZ_MODE | str | No | None | Authorization method to use. If not defined no authorization check is implemented and all endpoints can be access by any authenticated user (if authentication is enabled). Allowed values: _opa_ (uses OPA) |
| TRUSTED_IDP_LIST | list of str (URI format) | Yes | [] | List of the application trusted identity providers |
| API_KEY | str | No | None | API Key to set into the header field 'X-API-Key'. This authentication and authorization method is enabled only if this variable is set |
| IDP_TIMEOUT | int | Yes | 5 | Timeout for identity providers communication |
| OPA_AUTHZ_URL | str (URI format) | No | http://localhost:8181/v1/data/fed_mgr | Open Policy Agent service roles authorization URL. Mandatory if `AUTHZ_MODE` is _opa_ |
| OPA_TIMEOUT | int | No | 5 | Timeout for OPA service communication |
| KAFKA_ENABLE | bool | No | False | Enable kafka communication |
| KAFKA_BOOTSTRAP_SERVERS | str | No | localhost:9092 | Kafka server hostnames. DNS name and port. Can be a comma separeted list of DNS names |
| KAFKA_RALLY_RESULTS_TOPIC | str | No | rally_results | Kafka topic with the results of the rally tests performed over the federated resource providers
| KAFKA_TOPIC_TIMEOUT | int | No | 1000 | Number of ms to wait when reading published messages |
| KAFKA_MAX_REQUEST_SIZE | int | No | 104857600 | Maximum size of a request to send to kafka (B)
| KAFKA_CLIENT_NAME | str | No | fedmgr | Client name to use when connecting to kafka |
| KAFKA_ALLOW_AUTO_CREATE_TOPICS | bool | No | False | Enable automatic creation of new topics if not yet in kafka |
| KAFKA_SSL_ENABLE | bool | No | False | Enable SSL connection with kafka |
| KAFKA_SSL_CACERT_PATH | str | No | None | Path to the SSL CA cert file. Mandatory if `KAFKA_SSL_ENABLE` is True |
| KAFKA_SSL_CERT_PATH | str | No | None | Path to the SSL cert file. Mandatory if `KAFKA_SSL_ENABLE` is True |
| KAFKA_SSL_KEY_PATH | str | No | None | Path to the SSL Key file. Mandatory if `KAFKA_SSL_ENABLE` is True |
| KAFKA_SSL_PASSWORD | str | No | None | SSL password for encrypted certs |

## Developers

In this section we will give a set of instructions of the developers of the application.

Requirements:
- python >= 3.12
- [poetry](https://python-poetry.org/) >= 2.1: needed to install, update and delete python packages.

Within the python libraries that will be installed in development mode there are some handful development tools
- [ruff](https://docs.astral.sh/ruff/): needed to check linting and code formatting.
- [pytest](https://docs.pytest.org/en/stable/): test suite to run unit and functional tests.
- [pre-commit](https://pre-commit.com/): framework for managing and maintaining multi-language pre-commit hooks.

Prepare your environment as defined in [Local mode](#local-mode) section. **Since you are installing the dependencies in developmente mode, omit the `--without dev` section when installing the dependencies.**

**The first time you clone this project, after you have installed the python packages, run `pre-commit install` to install and enable the pre-commit hooks.**

If you want to use devcontainers, the application already has a configuration to develop using containers. This is stored in the `.devcontainer` directory and is based on the `docker/compose.yaml` example.

### Run the application

If you are using VSCode, the project already has a `launch.json` file with the **FastAPI App** configuration. This configuration runs the application in development mode and enables the usage of the debugger.

Otherwise, you can manually run the application in development mode: 

```bash
fastapi dev fed_mgr/main.py
```

### Use a SQLite DB

By default the application use an in-memory SQLite DB. If you want to persist these data on a file you just need to set the `DB_URL` environment variable to point to a file (e.g. `sqlite+pysqlite:///database.db`). The file can not exist, on start up it will be generated by the application.

### Use a MySQL DB

If yu want to use a MySQL DB to store the application data and persist its data you can use the [mysql](https://hub.docker.com/_/mysql/) docker image. The containerized instance of MySQL needs a volume to store the data and the passwords to create the DB. The username and password defined here will be used by the Federation-Manager to connect to this DB.

```bash
docker volume create db-data
docker run \
  -p 3306:3306 \
  -v db-data:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=changeit \
  -e MYSQL_DATABASE=fed_mgr \
  -e MYSQL_USER=fed-mgr \
  -e MYSQL_PASSWORD=changeit \
  mysql:8
```

### DB migrations

DB migrations are managed through the [alembic](https://alembic.sqlalchemy.org/en/latest/) library.

When changing the DB schema (add columns, remove tables and so on), update the tests related to models and schemas and write a new migration for alembic. To autogenerate the migration starting from the python models run:

```bash
alembic revision --autogenerate -m "<message>"
```

This command will generate a new file under `alembic/versions` directory. **Review the newly generated file.** If the content of the file is correct, apply the migration:

```bash
alembic upgrade head
```

> If in your DB models definition you define dialects-based operations, when writing the migration file verify that it works for all the application's supported DB dialects (currently *sqlite* and *mysql*).

**When switching between branches, DB versions may differ. In that cases you may need to downgrade or upgrade the DB to a specific DB version: `alembic upgrade <version-id>` or `alembic downgrade <version-id>`. For downgrade operations, these should be usually done *before* changing branch.**

### Run Kafka



### Run OPA

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

### Run tests

The application's tests makes use of the [pytest](https://docs.pytest.org/en/stable/) library. Tests are located in the `tests` directory and largely expolit fixtures and mocks. Here some examples on how to run tests:

To run all tests:

```bash
pytest
```

To run all the tests in a specific folder and subfolder:

```bash
pytest /tests/v1/models/
```

To run all the tests in a specific file:

```bash
pytest /tests/auth.py
```

To run a specific test:

```bash
pytest /tests/auth.py::test_check_authentication_none
```

The coverage calculation is available thorugh the [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) library. To check the tests' coverage:

```bash
pytest --cov
```
