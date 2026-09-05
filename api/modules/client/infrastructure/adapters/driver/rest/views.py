from dataclasses import asdict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from composition.container import get_app_client_container
from modules.client.application.ports.driver.add_address_ports import AddAddressCommand
from modules.client.application.ports.driver.create_client_ports import CreateClientCommand
from modules.client.application.ports.driver.remove_address_ports import RemoveAddressCommand
from modules.client.application.ports.driver.set_default_address_ports import (
    SetDefaultAddressCommand,
)
from modules.client.application.ports.driver.update_address_ports import UpdateAddressCommand
from modules.client.application.ports.driver.update_client_ports import UpdateClientCommand
from modules.client.application.ports.driver.delete_client_ports import DeleteClientCommand
from modules.client.application.ports.driver.get_client_ports import GetClientQuery
from modules.client.application.ports.driver.list_clients_ports import ListClientsQuery
from modules.client.domain.errors.client_errors import ClientNotFoundError

from .serializers import (
    AddressRequestSerializer,
    CreateClientRequestSerializer,
    UpdateClientRequestSerializer,
)


def _serialize_client(client) -> dict:
    return {
        "id": client.id,
        "name": client.name,
        "lastName": client.last_name,
        "phoneNumber": client.phone_number,
    }


class ClientListView(APIView):
    def post(self, request):
        serializer = CreateClientRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreateClientCommand(**serializer.validated_data)
        response = get_app_client_container().create_client.execute(command)

        return Response(asdict(response), status=status.HTTP_201_CREATED)

    def get(self, request):
        search = request.query_params.get("search")
        query = ListClientsQuery(search=search)
        clients = get_app_client_container().list_clients.execute(query)
        return Response([_serialize_client(c) for c in clients], status=status.HTTP_200_OK)


class ClientDetailView(APIView):
    def get(self, request, client_id: str):
        query = GetClientQuery(client_id=client_id)
        try:
            client = get_app_client_container().get_client.execute(query)
        except ClientNotFoundError:
            return Response(
                {"detail": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(_serialize_client(client), status=status.HTTP_200_OK)

    def patch(self, request, client_id: str):
        serializer = UpdateClientRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = UpdateClientCommand(client_id=client_id, **serializer.validated_data)
        response = get_app_client_container().update_client.execute(command)

        return Response(asdict(response), status=status.HTTP_200_OK)

    def delete(self, request, client_id: str):
        command = DeleteClientCommand(client_id=client_id)
        try:
            get_app_client_container().delete_client.execute(command)
        except ClientNotFoundError:
            return Response(
                {"detail": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientAddressListView(APIView):
    def post(self, request, client_id: str):
        serializer = AddressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = AddAddressCommand(client_id=client_id, **serializer.validated_data)
        response = get_app_client_container().add_address.execute(command)

        return Response(asdict(response), status=status.HTTP_201_CREATED)


class ClientAddressDetailView(APIView):
    def patch(self, request, client_id: str, address_id: str):
        serializer = AddressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        data.pop("is_default", None)

        command = UpdateAddressCommand(client_id=client_id, address_id=address_id, **data)
        response = get_app_client_container().update_address.execute(command)

        return Response(asdict(response), status=status.HTTP_200_OK)

    def delete(self, request, client_id: str, address_id: str):
        command = RemoveAddressCommand(client_id=client_id, address_id=address_id)
        get_app_client_container().remove_address.execute(command)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientAddressSetDefaultView(APIView):
    def post(self, request, client_id: str, address_id: str):
        command = SetDefaultAddressCommand(client_id=client_id, address_id=address_id)
        response = get_app_client_container().set_default_address.execute(command)

        return Response(asdict(response), status=status.HTTP_200_OK)
