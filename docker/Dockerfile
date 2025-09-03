ARG PYTHON_VERSION=3.12
ARG PYTHON_VARIANT=slim

# Install poetry
FROM python:${PYTHON_VERSION}-${PYTHON_VARIANT} AS poetry

ARG POETRY_VERSION=2.1.4

ENV POETRY_HOME=/opt/poetry \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH=${PATH}:/opt/poetry/bin

RUN python -m ensurepip --upgrade \
    && python -m pip install --upgrade setuptools pip poetry

# Stage used in production with the service
FROM poetry

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock ./README.md /app/
COPY ./fed_mgr /app/fed_mgr

RUN poetry install --without dev --with rest-api,mysql

CMD ["fastapi", "run", "/app/fed_mgr/main.py", "--port", "80"]
