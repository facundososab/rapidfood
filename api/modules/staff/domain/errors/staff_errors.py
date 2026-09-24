class StaffError(Exception):
    """Base error for the staff domain."""


class StaffDomainError(StaffError):
    pass


class StaffNotFoundError(StaffDomainError):
    def __init__(self, supabase_auth_id: str) -> None:
        super().__init__(f"Staff member with Supabase auth id '{supabase_auth_id}' not found")
        self.supabase_auth_id = supabase_auth_id