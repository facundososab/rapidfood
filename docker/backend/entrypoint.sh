#!/bin/sh
set -eu

echo "Applying Prisma migrations..."
uv run prisma migrate deploy --schema shared/infrastructure/prisma/schema.prisma

echo "Starting Django dev server on :8000"
exec uv run python manage.py runserver 0.0.0.0:8000