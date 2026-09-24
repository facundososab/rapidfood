"""Supabase Auth settings (env-driven, infrastructure only)."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SupabaseAuthSettings:
    url: Optional[str] = None
    anon_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    service_role_key: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SupabaseAuthSettings":
        return cls(
            url=os.environ.get("SUPABASE_URL"),
            anon_key=os.environ.get("SUPABASE_ANON_KEY"),
            jwt_secret=os.environ.get("SUPABASE_JWT_SECRET"),
            service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
        )