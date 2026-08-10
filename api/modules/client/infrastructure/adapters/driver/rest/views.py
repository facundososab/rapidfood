import uuid
from dataclasses import asdict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    CreateClientRequestSerializer,
    UpdateClientRequestSerializer,
    AddressRequestSerializer,
)
from modules.client.application.ports.driver.client_ports import (
    CreateClientCommand,
    UpdateClientCommand,
)
from modules.client.application.ports.driver.address_ports import (
    AddAddressCommand,
    UpdateAddressCommand,
    RemoveAddressCommand,
    SetDefaultAddressCommand,
)
from modules.client.configuration.container import ClientContainer


class ClientListCreateView(APIView):
    def post(self, request):
        serializer = CreateClientRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = CreateClientCommand(**serializer.validated_data)
        use_case = ClientContainer.create_client_use_case()
        response = use_case.execute(command)
        
        return Response(asdict(response), status=status.HTTP_201_CREATED)
        
    def get(self, request):
        phone_number = request.query_params.get("phone_number")
        if phone_number:
            query_adapter = ClientContainer.client_query_adapter()
            client_dto = query_adapter.find_by_phone_number(phone_number)
            if client_dto is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(asdict(client_dto), status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ClientDetailView(APIView):
    def patch(self, request, pk):
        serializer = UpdateClientRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = UpdateClientCommand(client_id=pk, **serializer.validated_data)
        use_case = ClientContainer.update_client_use_case()
        response = use_case.execute(command)
        
        return Response(asdict(response), status=status.HTTP_200_OK)


class ClientAddressListView(APIView):
    def post(self, request, pk):
        serializer = AddressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = AddAddressCommand(client_id=pk, **serializer.validated_data)
        use_case = ClientContainer.add_address_use_case()
        response = use_case.execute(command)
        
        return Response(asdict(response), status=status.HTTP_201_CREATED)


class ClientAddressDetailView(APIView):
    def patch(self, request, pk, address_id):
        serializer = AddressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # is_default is not modified via patch on the address resource, 
        # but we can filter it out if present
        data = serializer.validated_data
        data.pop("is_default", None)
        
        command = UpdateAddressCommand(client_id=pk, address_id=address_id, **data)
        use_case = ClientContainer.update_address_use_case()
        response = use_case.execute(command)
        
        return Response(asdict(response), status=status.HTTP_200_OK)
        
    def delete(self, request, pk, address_id):
        command = RemoveAddressCommand(client_id=pk, address_id=address_id)
        use_case = ClientContainer.remove_address_use_case()
        use_case.execute(command)
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientAddressSetDefaultView(APIView):
    def post(self, request, pk, address_id):
        command = SetDefaultAddressCommand(client_id=pk, address_id=address_id)
        use_case = ClientContainer.set_default_address_use_case()
        response = use_case.execute(command)
        
        return Response(asdict(response), status=status.HTTP_200_OK)
