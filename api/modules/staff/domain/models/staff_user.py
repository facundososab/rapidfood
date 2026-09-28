"""Staff module — restaurant personnel & roles.

Identity comes from Supabase Auth (JWT); this module owns the authorization
side (who is staff, with which role) in the Prisma-owned database.
"""

from dataclasses import dataclass
from enum import Enum


class StaffRole(Enum):
    ADMIN = "ADMIN"
    CASHIER = "CASHIER"
    KITCHEN = "KITCHEN"


@dataclass
class StaffUser:
    id: str
    supabase_auth_id: str
    email: str
    name: str
    role: StaffRole
    business_config_id: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Name cannot be blank")
        if not self.email.strip():
            raise ValueError("Email cannot be blank")
        if not isinstance(self.role, StaffRole):
            raise ValueError("Role must be a StaffRole")

    @classmethod
    def create(
        cls,
        staff_id: str,
        supabase_auth_id: str,
        email: str,
        name: str,
        role: StaffRole,
        business_config_id: str | None = None,
    ) -> "StaffUser":
        return cls(
            id=staff_id,
            supabase_auth_id=supabase_auth_id,
            email=email.strip(),
            name=name.strip(),
            role=role,
            business_config_id=business_config_id,
        )