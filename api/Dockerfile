# Rapidfood API — Django 5/DRF HTTP shell + Prisma Client Python.
# Build context is the repo root: docker compose builds it as `api/Dockerfile`.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

# prisma-client-py spawns an embedded Node (nodeenv + npm prisma CLI) on first
# run; the node binary needs libatomic.so.1, missing from python slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libatomic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first (cached layer): project metadata + lockfile.
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

# Application code.
COPY api/ /app/

# Generate the typed Prisma client. Default output patches the installed
# `prisma` package (the app imports `from prisma import Prisma`).
# NOTE: the CLI needs --schema; `prisma generate` alone does NOT find it.
RUN uv run prisma generate --schema shared/infrastructure/prisma/schema.prisma

COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]