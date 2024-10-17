ARG PYTHON_VERSION=3.10
ARG POETRY_VERSION=1.8.3

# Create requirements.txt from poetry dependencies
FROM ghcr.io/withlogicco/poetry:${POETRY_VERSION}-python-${PYTHON_VERSION}-slim AS requirements

WORKDIR /tmp

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export \
    -f requirements.txt \
    --output requirements.txt \
    --without-hashes \
    --without dev

# Stage used in production with no kubernetes
FROM tiangolo/uvicorn-gunicorn-fastapi:python${PYTHON_VERSION}-slim AS production

RUN apt-get update \
    && apt-get install -y git \
    && apt-get clean

WORKDIR /app/

COPY --from=requirements /tmp/requirements.txt /app/requirements.txt

# Upgrade pip and install requirements
RUN pip install --user --upgrade pip==20.2.4 \
    && pip install --user --no-cache-dir --upgrade -r /app/requirements.txt

ENV PYTHONPATH="${PYTHONPATH}:/app"
ENV APP_MODULE=fed_mng.main:app

COPY ./fed_mng /app/fed_mng
