ARG PYTHON_VERSION=3.12
ARG POETRY_VERSION=2.1

FROM harbor.cloud.infn.it/datacloud-middleware/poetry:${POETRY_VERSION}-python${PYTHON_VERSION} AS base

RUN apt-get update \
    && apt-get --no-install-recommends install -y curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock ./README.md /app/
COPY ./fed_mgr /app/fed_mgr
COPY ./alembic.ini /app/
COPY ./alembic /app/alembic
COPY --chmod=+x ./docker/start.sh /app/

RUN poetry install --without dev --with rest-api,mysql

USER ${USERNAME}

CMD ["./start.sh"]
