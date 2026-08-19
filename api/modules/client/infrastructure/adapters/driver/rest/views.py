from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.client.application.ports.driver.delete_client_ports import (
    DeleteClientCommand,
)
from modules.client.application.ports.driver.get_client_ports import GetClientQuery
from modules.client.application.ports.driver.list_clients_ports import ListClientsQuery
from modules.client.domain.errors.client_errors import ClientNotFoundError
from composition.container import get_app_client_container


def _serialize_client(client) -> dict:
    return {
        "id": client.id,
        "name": client.name,
        "lastName": client.lastName,
        "phoneNumber": client.phoneNumber,
    }


class ClientListView(APIView):
    def get(self, request):
        query = ListClientsQuery(search=request.query_params.get("search"))

        results = get_app_client_container().list_clients.execute(query)
        return Response([_serialize_client(c) for c in results])


class ClientDetailView(APIView):
    def get(self, request, client_id: str):
        query = GetClientQuery(client_id=client_id)

        container = get_app_client_container()
        try:
            client = container.get_client.execute(query)
        except ClientNotFoundError:
            return Response(
                {"detail": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(_serialize_client(client))

    def delete(self, request, client_id: str):
        command = DeleteClientCommand(client_id=client_id)

        container = get_app_client_container()
        try:
            container.delete_client.execute(command)
        except ClientNotFoundError:
            return Response(
                {"detail": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)