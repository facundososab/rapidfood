from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from composition.container import get_app_staff_container
from modules.staff.application.ports.driver.get_current_staff_ports import (
    GetStaffBySupabaseAuthIdQuery,
)
from modules.staff.domain.errors.staff_errors import StaffNotFoundError


def _serialize_staff(staff) -> dict:
    return {
        "id": staff.id,
        "email": staff.email,
        "name": staff.name,
        "role": staff.role.value,
        "businessConfigId": staff.business_config_id,
    }


class MeView(APIView):
    """Current staff member: the Supabase identity resolved to a staff row."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = GetStaffBySupabaseAuthIdQuery(supabase_auth_id=request.user.id)
        try:
            staff = get_app_staff_container().get_current_staff.execute(query)
        except StaffNotFoundError:
            return Response(
                {"error": "Esta cuenta no corresponde al personal del restaurante"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_serialize_staff(staff), status=status.HTTP_200_OK)