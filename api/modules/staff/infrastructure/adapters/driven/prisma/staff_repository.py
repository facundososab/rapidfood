from modules.staff.application.ports.driven.staff_repository_port import (
    StaffRepositoryPort,
)
from modules.staff.domain.models.staff_user import StaffUser
from modules.staff.infrastructure.adapters.driven.prisma.mappers.staff_mapper import (
    StaffMapper,
)
from shared.infrastructure.prisma.db import db


class PrismaStaffRepository(StaffRepositoryPort):
    def get_by_supabase_auth_id(self, supabase_auth_id: str) -> StaffUser | None:
        record = db.client.staff.find_unique(where={"supabaseAuthId": supabase_auth_id})
        return StaffMapper.to_domain(record) if record is not None else None

    def get_by_email(self, email: str) -> StaffUser | None:
        record = db.client.staff.find_unique(where={"email": email})
        return StaffMapper.to_domain(record) if record is not None else None