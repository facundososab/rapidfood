"""pytest-django <-> Prisma bridge.

pytest-django runs on Django's sqlite `:memory:` placeholder (never touches
Postgres, per design). Prisma owns the real data layer, so DB tests target a
dedicated Postgres test database (`test_<db>`) derived from DATABASE_URL.

This module:
  1. ensures the test database exists in Postgres — pytest-django does NOT
     create it because Django's backend here is sqlite `:memory:`,
  2. runs `prisma migrate deploy` against it so ALL Prisma tables exist
     (Django's runner never creates Prisma tables),
  3. exposes a session-scoped Prisma client bound to the test database.

DB tests are marked `db` and are NOT wrapped in Django transactions (Prisma
owns its own connection pool); each test cleans up after itself.
"""

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import psycopg
from psycopg import sql
import pytest
from prisma import Prisma


PRISMA_SCHEMA = (
    Path(__file__).resolve().parents[1] / "schema.prisma"
)


def _test_database_url() -> str:
    try:
        raw = os.environ["DATABASE_URL"]
    except KeyError:
        raise RuntimeError(
            "DATABASE_URL is not set. Create .env (`cp .env.example .env`) "
            "and make sure `docker compose up -d db` is running."
        ) from None
    parsed = urlparse(raw)
    return parsed._replace(path=f"/test_{parsed.path.lstrip('/')}").geturl()


def _ensure_test_database_exists(test_url: str) -> None:
    """Create the test database if missing (connect via the maintenance DB)."""
    parsed = urlparse(test_url)
    dbname = parsed.path.lstrip("/")
    maintenance_url = parsed._replace(path="/postgres").geturl()
    # Explicit connect_timeout: Docker Desktop keeps a proxy listening on the
    # port even when the container is stopped, so a plain connect would hang
    # instead of failing fast. 5s x 2 stacks (~10s) = "fast failure" without
    # Postgres.
    with psycopg.connect(maintenance_url, autocommit=True, connect_timeout=5) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)
        ).fetchone()
        if not exists:
            conn.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname))
            )


@pytest.fixture(scope="session", autouse=True)
def prisma_test_db(django_db_setup, django_db_blocker):
    """pytest-django sets Django up; we then create the test DB + ALL Prisma tables."""
    test_url = _test_database_url()
    _ensure_test_database_exists(test_url)
    with django_db_blocker.unblock():
        subprocess.run(
            [
                "uv",
                "run",
                "prisma",
                "migrate",
                "deploy",
                "--schema",
                str(PRISMA_SCHEMA),
            ],
            env={**os.environ, "DATABASE_URL": test_url},
            check=True,
        )
    yield  # pytest-django tears the test DB down at session end


@pytest.fixture(scope="session")
def db(prisma_test_db):
    """Session-scoped Prisma client bound to the test database."""
    os.environ["DATABASE_URL"] = _test_database_url()  # resolved by Prisma at connect()
    client = Prisma()
    client.connect()
    yield client
    client.disconnect()
