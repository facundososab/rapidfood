#!/bin/sh
set -eu

echo "Regenerating Prisma client..."
uv run prisma generate --schema shared/infrastructure/prisma/schema.prisma

echo "Applying Prisma migrations..."
uv run prisma migrate deploy --schema shared/infrastructure/prisma/schema.prisma

# Regenerate the typed client on every boot: the schema is bind-mounted in dev,
# so it can change without an image rebuild and the running client would go stale
# (AttributeError on the new models). Idempotent and offline (engines are baked).
echo "Generating Prisma client..."
uv run prisma generate --schema shared/infrastructure/prisma/schema.prisma

echo "Starting Django dev server on :8000"
exec uv run python manage.py runserver 0.0.0.0:8000