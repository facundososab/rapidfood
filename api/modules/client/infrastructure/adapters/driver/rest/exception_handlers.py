from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from modules.client.domain.errors.client_errors import (
    ClientDomainError,
    ClientNotFoundError,
    ClientAlreadyExistsError,
    AddressNotFoundError,
    AddressNotOwnedByClientError,
)

def client_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, ClientDomainError):
        if isinstance(exc, ClientNotFoundError) or isinstance(exc, AddressNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, ClientAlreadyExistsError):
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(exc, AddressNotOwnedByClientError):
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            
        return Response(
            {"error": str(exc)},
            status=status_code,
        )

    return None
