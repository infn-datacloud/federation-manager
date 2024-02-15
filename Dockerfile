# Create requirements.txt from poetry dependencies
FROM python:3.10-slim AS requirements

WORKDIR /tmp

RUN pip install poetry

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# Stage used in production
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10-slim AS production

WORKDIR /app/

COPY --from=requirements /tmp/requirements.txt /app/requirements.txt

RUN apt-get update \
    && apt-get install -y git \
    && apt-get clean

RUN pip install --user --upgrade pip==20.2.4 \
    && pip install --user --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./fed_mng /app/fed_mng

ENV PYTHONPATH=/app
ENV APP_MODULE=fed_mng.main:app
