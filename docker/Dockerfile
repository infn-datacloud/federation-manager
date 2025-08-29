ARG PYTHON_VERSION=3.12
ARG POETRY_VERSION=1.8.3

# Install packages using poetry
FROM ghcr.io/withlogicco/poetry:${POETRY_VERSION}-python-${PYTHON_VERSION}-slim AS builder

COPY ./pyproject.toml ./poetry.lock ./README.md /usr/src/app/
COPY ./fed_mgr /usr/src/app/fed_mgr

RUN poetry install --without dev --with rest-api,mysql

# Stage used in production with the service
FROM python:${PYTHON_VERSION}-slim AS production

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app/

COPY --from=builder /usr/local/ /usr/local
COPY ./fed_mgr ./fed_mgr

CMD ["fastapi", "run", "/app/fed_mgr/main.py", "--port", "80"]