ARG PYTHON_VERSION=3.12
ARG POETRY_VERSION=2.1

FROM harbor.cloud.infn.it/datacloud-middleware/poetry:${POETRY_VERSION}-python${PYTHON_VERSION} AS base

RUN apt-get update \
    && apt-get install -y curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock ./README.md /app/
COPY ./fed_mgr /app/fed_mgr

RUN poetry install --without dev --with rest-api,mysql

USER ${USERNAME}

CMD ["fastapi", "run", "/app/fed_mgr/main.py", "--port", "80"]
