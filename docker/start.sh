#!/bin/bash

alembic current --check-heads || alembic upgrade head \
    && fastapi run /app/fed_mgr/main.py --port 80
