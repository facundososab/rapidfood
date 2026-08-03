"""DB smoke test — proves Prisma tables exist via `prisma migrate deploy`.

Uses the session `db` fixture (Prisma client bound to test_<db>). Cleans up
after itself; NOT wrapped in Django transactions (Prisma owns its pool).
"""

import pytest

pytestmark = pytest.mark.db


def test_prisma_tables_exist_via_migrate_deploy(db):
    created = db.client.create(
        data={"name": "Ana", "lastName": "Gomez", "phoneNumber": "+54 11 5555 0001"}
    )
    try:
        assert db.client.find_unique(where={"id": created.id}) is not None
    finally:
        db.client.delete(where={"id": created.id})
