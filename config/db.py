"""Shared Prisma client (infrastructure only).

The lazy singleton lives here so every outbound adapter binds to ONE Prisma
instance. It is injected into adapters via constructors at the composition
root (``apps/*/composition/container.py``) — use cases never import this
module directly.

``DATABASE_URL`` is resolved by Prisma at ``connect()`` time, so tests can
point the singleton at a test database by overriding the environment variable
before the first connect.
"""

from __future__ import annotations

from prisma import Prisma


class Database:
    """Lazy Prisma client singleton."""

    def __init__(self) -> None:
        self._client: Prisma | None = None

    @property
    def client(self) -> Prisma:
        if self._client is None:
            self._client = Prisma()
            self._client.connect()
        return self._client

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.disconnect()
            self._client = None


# Module-level singleton (infrastructure only; never used by use cases).
db = Database()
