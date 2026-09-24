from dataclasses import dataclass


@dataclass(frozen=True)
class GetStaffBySupabaseAuthIdQuery:
    supabase_auth_id: str