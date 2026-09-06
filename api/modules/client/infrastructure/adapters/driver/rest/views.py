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
from modules.client.domain.errors.client_errors import (
    ClientNotFoundError,
    ClientDomainError,
    AddressNotFoundError,
    AddressNotOwnedByClientError,
)
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


class CreateClientView(APIView):
    def post(self, request):
        serializer = CreateClientRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            command = CreateClientCommand(**serializer.validated_data)
            response = get_app_client_container().create_client.execute(command)
            return Response(asdict(response), status=status.HTTP_201_CREATED)
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ListClientsView(APIView):
    def get(self, request):
        search = request.query_params.get("search")
        query = ListClientsQuery(search=search)
        clients = get_app_client_container().list_clients.execute(query)
        return Response([_serialize_client(c) for c in clients], status=status.HTTP_200_OK)


class GetClientView(APIView):
    def get(self, request, client_id: str):
        query = GetClientQuery(client_id=client_id)
        try:
            client = get_app_client_container().get_client.execute(query)
            return Response(_serialize_client(client), status=status.HTTP_200_OK)
        except ClientNotFoundError:
            return Response(
                {"error": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateClientView(APIView):
    def patch(self, request, client_id: str):
        serializer = UpdateClientRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            command = UpdateClientCommand(client_id=client_id, **serializer.validated_data)
            response = get_app_client_container().update_client.execute(command)
            return Response(asdict(response), status=status.HTTP_200_OK)
        except ClientNotFoundError:
            return Response(
                {"error": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteClientView(APIView):
    def delete(self, request, client_id: str):
        command = DeleteClientCommand(client_id=client_id)
        try:
            get_app_client_container().delete_client.execute(command)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ClientNotFoundError:
            return Response(
                {"error": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddAddressView(APIView):
    def post(self, request, client_id: str):
        serializer = AddressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            command = AddAddressCommand(client_id=client_id, **serializer.validated_data)
            response = get_app_client_container().add_address.execute(command)
            return Response(asdict(response), status=status.HTTP_201_CREATED)
        except ClientNotFoundError:
            return Response(
                {"error": "El cliente no existe"}, status=status.HTTP_404_NOT_FOUND
            )
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateAddressView(APIView):
    def patch(self, request, client_id: str, address_id: str):
        serializer = AddressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        data.pop("is_default", None)

        try:
            command = UpdateAddressCommand(client_id=client_id, address_id=address_id, **data)
            response = get_app_client_container().update_address.execute(command)
            return Response(asdict(response), status=status.HTTP_200_OK)
        except (ClientNotFoundError, AddressNotFoundError):
            return Response(
                {"error": "El cliente o la dirección no existen"}, status=status.HTTP_404_NOT_FOUND
            )
        except AddressNotOwnedByClientError:
            return Response(
                {"error": "La dirección no pertenece a este cliente"}, status=status.HTTP_403_FORBIDDEN
            )
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RemoveAddressView(APIView):
    def delete(self, request, client_id: str, address_id: str):
        command = RemoveAddressCommand(client_id=client_id, address_id=address_id)
        try:
            get_app_client_container().remove_address.execute(command)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (ClientNotFoundError, AddressNotFoundError):
            return Response(
                {"error": "El cliente o la dirección no existen"}, status=status.HTTP_404_NOT_FOUND
            )
        except AddressNotOwnedByClientError:
            return Response(
                {"error": "La dirección no pertenece a este cliente"}, status=status.HTTP_403_FORBIDDEN
            )
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SetDefaultAddressView(APIView):
    def post(self, request, client_id: str, address_id: str):
        command = SetDefaultAddressCommand(client_id=client_id, address_id=address_id)
        try:
            response = get_app_client_container().set_default_address.execute(command)
            return Response(asdict(response), status=status.HTTP_200_OK)
        except (ClientNotFoundError, AddressNotFoundError):
            return Response(
                {"error": "El cliente o la dirección no existen"}, status=status.HTTP_404_NOT_FOUND
            )
        except AddressNotOwnedByClientError:
            return Response(
                {"error": "La dirección no pertenece a este cliente"}, status=status.HTTP_403_FORBIDDEN
            )
        except ClientDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
