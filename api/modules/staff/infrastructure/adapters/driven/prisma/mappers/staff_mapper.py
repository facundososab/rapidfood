from modules.staff.domain.models.staff_user import StaffRole, StaffUser


class StaffMapper:
    """Translates the Prisma ``staff`` record to the domain StaffUser.

    Column/field names follow the Prisma client (camelCase properties mapped
    from snake_case DB columns).
    """

    @staticmethod
    def to_domain(record) -> StaffUser:
        return StaffUser(
            id=record.id,
            supabase_auth_id=record.supabaseAuthId,
            email=record.email,
            name=record.name,
            role=_to_domain_role(record.role),
            business_config_id=record.businessConfigId,
        )


def _to_domain_role(role) -> StaffRole:
    value = getattr(role, "value", role)
    try:
        return StaffRole(value)
    except ValueError:
        return StaffRole(str(value).upper())