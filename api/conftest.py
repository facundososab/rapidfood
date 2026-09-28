"""Prisma test-database fixtures for every ``api/**`` test.

The original definitions live in
``api/shared/infrastructure/prisma/tests/conftest.py`` but a ``conftest.py`` is
only visible inside its own directory. Module integration tests (coupons,
payments) request the ``db`` fixture, so without this file they silently
resolved pytest-django's ``db`` fixture — which yields ``None`` — and the
repository wrappers fell back to the DEV database.

This conftest re-exposes the same fixtures at the ``api/`` root. The session
fixture is intentionally NOT autouse here: only tests that request ``db`` need
Postgres, so pure unit tests keep running without a database.
"""

from __future__ import annotations

import os
import subprocess

import pytest
from prisma import Prisma

from shared.infrastructure.prisma.tests.conftest import (
    PRISMA_SCHEMA,
    _ensure_test_database_exists,
    _reset_test_schema,
    _test_database_url,
)


@pytest.fixture(scope="session")
def prisma_test_db(django_db_setup, django_db_blocker):
    """Create/migrate the dedicated Prisma test database once per session."""
    test_url = _test_database_url()

    _ensure_test_database_exists(test_url)
    _reset_test_schema(test_url)

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
            env={
                **os.environ,
                "DATABASE_URL": test_url,
            },
            check=True,
        )

    yield


@pytest.fixture(scope="session")
def db(prisma_test_db):
    """Session-scoped Prisma client bound to the test database."""
    test_url = _test_database_url()

    previous_database_url = os.environ.get("DATABASE_URL")

    os.environ["DATABASE_URL"] = test_url

    client = Prisma()
    client.connect()

    try:
        yield client
    finally:
        client.disconnect()

        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
