# Reglas por capa


### Domain

Ubicación:

```text
domain/
├── models/
├── errors/
└── ports/
```

Contiene las reglas centrales del negocio.

Puede incluir:

- Entidades.
- Value objects.
- Enumeraciones de dominio.
- Servicios de dominio.
- Excepciones de dominio.
- Políticas y especificaciones.
- Puertos estrictamente necesarios para ejecutar lógica de dominio.

No debe importar:

- Django.
- Django REST Framework.
- Repositorios concretos.
- Serializers.
- Views.
- Modelos ORM.
- Requests HTTP.
- Librerías de infraestructura.

Ejemplo de entidad:

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than zero")

        if self.unit_price < Decimal("0"):
            raise ValueError("Unit price cannot be negative")

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity
```

Las entidades deben proteger sus invariantes. No se deben modificar libremente desde otras capas cuando exista una operación de dominio para hacerlo.

### Domain models

Ubicación:

```text
domain/models/
```

Usar para:

- Entidades.
- Value objects.
- Agregados.
- Enums.
- Servicios de dominio relacionados directamente con el modelo.

Ejemplos:

```text
domain/models/client.py
domain/models/address.py
domain/models/order.py
domain/models/order_item.py
domain/models/money.py
domain/models/order_status.py
```

Evitar archivos genéricos demasiado grandes como:

```text
entities.py
models.py
utils.py
```

Preferir un archivo por concepto principal cuando el módulo crezca.

### Domain errors

Ubicación:

```text
domain/errors/
```

Debe contener errores propios del negocio.

Ejemplos:

```python
class DomainError(Exception):
    pass


class InvalidOrderStateError(DomainError):
    pass


class ProductUnavailableError(DomainError):
    pass
```

No usar excepciones HTTP dentro del dominio:

```python
# Incorrecto
from rest_framework.exceptions import ValidationError
```

Los errores de dominio serán traducidos a respuestas HTTP por el adaptador REST.

### Domain ports

Ubicación:

```text
domain/ports/
```

Usar únicamente para abstracciones requeridas directamente por una regla de dominio.

Ejemplos:

- Política de cálculo dependiente de una fuente externa.
- Servicio de dominio abstracto.
- Verificación externa imprescindible para una operación del agregado.

No colocar aquí repositorios usados solamente por casos de uso. Esos pertenecen a:

```text
application/ports/driven/
```

En la mayoría de los casos, `domain/ports/` permanecerá vacío.

## Application

La capa de aplicación orquesta el dominio.

Contiene:

- Casos de uso.
- Commands.
- Queries.
- Responses.
- Puertos de entrada.
- Puertos de salida.
- Coordinación entre entidades y servicios.

No debe contener:

- Reglas centrales que pertenezcan a entidades.
- Código HTTP.
- Serializers de DRF.
- Modelos Django ORM.
- Consultas directas a la base de datos.
- Implementaciones concretas de servicios externos.

### Driver ports

Ubicación:

```text
application/ports/driver/
```

Representan las operaciones disponibles para actores externos.

Los actores externos pueden ser:

- Una API REST.
- Un agente de IA.
- Un comando de consola.
- Una tarea programada.
- Otro bounded context.

Agrupar por submódulo o agregado:

```text
application/ports/driver/
├── client/
│   └── client_identity_ports.py
└── address/
    └── client_address_ports.py
```

Cada archivo puede contener:

- Command o Query.
- Response.
- Protocolo o interfaz del caso de uso.

Ejemplo:

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RegisterClientCommand:
    name: str
    phone: str


@dataclass(frozen=True)
class RegisterClientResponse:
    client_id: str
    name: str
    phone: str


class RegisterClientPort(Protocol):
    def execute(
        self,
        command: RegisterClientCommand,
    ) -> RegisterClientResponse:
        ...
```

Los commands deben utilizar tipos simples o value objects controlados.

No deben recibir:

- `HttpRequest`.
- Serializers.
- Modelos ORM.
- Objetos específicos de Django.

### Driven ports

Ubicación:

```text
application/ports/driven/
```

Representan dependencias que la aplicación necesita, pero cuya implementación no le interesa.

Ejemplos:

- Repositorios.
- Generadores de identificadores.
- Relojes.
- Clientes de IA.
- Gateways de mensajería.
- Proveedores de geocodificación.
- Servicios de notificación.
- Publicadores de eventos.

Ejemplo:

```python
from typing import Protocol

from modules.client.domain.models.client import Client


class ClientRepositoryPort(Protocol):
    def save(self, client: Client) -> None:
        ...

    def find_by_id(self, client_id: str) -> Client | None:
        ...

    def find_by_phone(self, phone: str) -> Client | None:
        ...
```

Los puertos deben expresar necesidades del negocio y no detalles tecnológicos.

Incorrecto:

```python
class ClientRepositoryPort:
    def filter_queryset(self, query: dict): ...
```

Correcto:

```python
class ClientRepositoryPort:
    def find_by_phone(self, phone: str): ...
```

### Use cases

Ubicación:

```text
application/use_cases/
```

Cada caso de uso debe representar una acción concreta del sistema.

Ejemplos:

```text
register_client_use_case.py
add_address_use_case.py
create_order_use_case.py
apply_coupon_use_case.py
send_conversation_message_use_case.py
```

Un caso de uso debe:

1. Recibir un command o query.
2. Validar precondiciones de aplicación.
3. Obtener entidades mediante puertos.
4. Invocar comportamiento del dominio.
5. Persistir mediante puertos.
6. Devolver una response independiente del framework.

Ejemplo:

```python
from modules.client.application.ports.driver.client.client_identity_ports import (
    RegisterClientCommand,
    RegisterClientPort,
    RegisterClientResponse,
)
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.application.ports.driven.id_generator_port import (
    IdGeneratorPort,
)
from modules.client.domain.errors.client_errors import ClientAlreadyExistsError
from modules.client.domain.models.client import Client


class RegisterClientUseCase(RegisterClientPort):
    def __init__(
        self,
        client_repository: ClientRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._client_repository = client_repository
        self._id_generator = id_generator

    def execute(
        self,
        command: RegisterClientCommand,
    ) -> RegisterClientResponse:
        existing_client = self._client_repository.find_by_phone(command.phone)

        if existing_client is not None:
            raise ClientAlreadyExistsError(command.phone)

        client = Client.create(
            client_id=self._id_generator.generate(),
            name=command.name,
            phone=command.phone,
        )

        self._client_repository.save(client)

        return RegisterClientResponse(
            client_id=client.id,
            name=client.name,
            phone=client.phone.value,
        )
```

## Infrastructure

La infraestructura contiene implementaciones concretas.

Puede depender de:

- Django.
- Django REST Framework.
- PostgreSQL.
- APIs externas.
- SDK de IA.
- Servicios de mensajería.
- Frameworks y librerías.

La infraestructura puede importar application y domain. Las capas internas no pueden importar infraestructura.

## Driver adapters

Ubicación:

```text
infrastructure/adapters/driver/
```

Reciben solicitudes desde el exterior y llaman a los puertos de entrada.

Ejemplos:

- REST.
- WebSockets.
- Management commands.
- Consumers de colas.
- Webhooks.
- Jobs.

### REST adapter

Ubicación:

```text
infrastructure/adapters/driver/rest/
```

Puede contener:

```text
views.py
serializers.py
urls.py
exception_handlers.py
```

Responsabilidades:

- Recibir HTTP.
- Validar formato de entrada.
- Convertir datos a commands o queries.
- Ejecutar el puerto de entrada.
- Convertir la response a JSON.
- Traducir errores de dominio a códigos HTTP.

La view no debe contener lógica de negocio.

Ejemplo:

```python
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.client.application.ports.driver.client.client_identity_ports import (
    RegisterClientCommand,
    RegisterClientPort,
)
from modules.client.infrastructure.adapters.driver.rest.serializers import (
    RegisterClientSerializer,
)


class RegisterClientView(APIView):
    register_client: RegisterClientPort

    def post(self, request: Request) -> Response:
        serializer = RegisterClientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = RegisterClientCommand(
            name=serializer.validated_data["name"],
            phone=serializer.validated_data["phone"],
        )

        result = self.register_client.execute(command)

        return Response(
            {
                "id": result.client_id,
                "name": result.name,
                "phone": result.phone,
            },
            status=status.HTTP_201_CREATED,
        )
```

Los serializers deben validar estructura y formato de transporte. Las reglas de negocio deben seguir en el dominio.

Ejemplo:

- El serializer puede validar que `quantity` sea un entero.
- La entidad debe validar que la cantidad sea mayor que cero.

## Driven adapters

Ubicación:

```text
infrastructure/adapters/driven/
```

Implementan puertos de salida.

Ejemplos:

```text
django_orm/
openai/
whatsapp/
email/
geocoding/
event_bus/
```

### Django ORM adapter

Ubicación:

```text
infrastructure/adapters/driven/django_orm/
```

Puede contener:

```text
models.py
client_repository.py
mappers.py
```

Los modelos Django representan persistencia, no el dominio.

Ejemplo:

```python
from django.db import models


class ClientModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = "clients"
```

El repositorio debe convertir entre modelos ORM y entidades de dominio:

```python
from modules.client.application.ports.driven.client_repository_port import (
    ClientRepositoryPort,
)
from modules.client.domain.models.client import Client
from modules.client.domain.models.phone import Phone
from modules.client.infrastructure.adapters.driven.django_orm.models import (
    ClientModel,
)


class DjangoClientRepository(ClientRepositoryPort):
    def save(self, client: Client) -> None:
        ClientModel.objects.update_or_create(
            id=client.id,
            defaults={
                "name": client.name,
                "phone": client.phone.value,
            },
        )

    def find_by_id(self, client_id: str) -> Client | None:
        model = ClientModel.objects.filter(id=client_id).first()

        if model is None:
            return None

        return self._to_domain(model)

    def find_by_phone(self, phone: str) -> Client | None:
        model = ClientModel.objects.filter(phone=phone).first()

        if model is None:
            return None

        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: ClientModel) -> Client:
        return Client(
            client_id=model.id,
            name=model.name,
            phone=Phone(model.phone),
        )
```

No devolver modelos ORM desde un repositorio de aplicación.

Incorrecto:

```python
def find_by_id(self, client_id: str) -> ClientModel:
    return ClientModel.objects.get(id=client_id)
```

Correcto:

```python
def find_by_id(self, client_id: str) -> Client | None:
    ...
```

## Configuration

Ubicación:

```text
configuration/
```

Responsabilidades:

- Registrar el módulo en Django.
- Crear adaptadores concretos.
- Instanciar casos de uso.
- Inyectar dependencias.
- Exponer el composition root del módulo.

Puede contener:

```text
apps.py
container.py
```

Ejemplo de container:

```python
from functools import lru_cache

from modules.client.application.use_cases.client.register_client_use_case import (
    RegisterClientUseCase,
)
from modules.client.infrastructure.adapters.driven.django_orm.client_repository import (
    DjangoClientRepository,
)
from shared.infrastructure.uuid_generator import UuidGenerator


class ClientContainer:
    def __init__(self) -> None:
        client_repository = DjangoClientRepository()
        id_generator = UuidGenerator()

        self.register_client = RegisterClientUseCase(
            client_repository=client_repository,
            id_generator=id_generator,
        )


@lru_cache(maxsize=1)
def get_client_container() -> ClientContainer:
    return ClientContainer()
```

No instanciar repositorios directamente dentro de las views.

Incorrecto:

```python
class RegisterClientView(APIView):
    def post(self, request):
        repository = DjangoClientRepository()
        use_case = RegisterClientUseCase(repository)
```

La composición debe centralizarse en `configuration/container.py`.

## Migraciones

Cada módulo mantiene sus propias migraciones:

```text
module/migrations/
```

Las migraciones pertenecen a la infraestructura de persistencia, aunque Django requiera una ubicación determinada para descubrirlas.

No colocar reglas de negocio en migraciones.

Las migraciones de datos deben ser:

- Deterministas.
- Reversibles cuando sea posible.
- Independientes de servicios externos.
- Seguras frente a datos existentes.

## Shared

Ubicación general:

```text
api/shared/
```

Solo debe contener elementos realmente compartidos y estables.

Puede incluir:

- `Money`.
- `Email`.
- `Phone`.
- Identificadores comunes.
- Reloj.
- Generador UUID.
- Tipos base.
- Errores técnicos comunes.
- Infraestructura transversal.

No mover algo a `shared` solamente porque dos módulos tengan clases parecidas.

Antes de compartir un concepto, comprobar que:

1. Tiene el mismo significado en ambos contextos.
2. Mantiene las mismas invariantes.
3. Cambiará por las mismas razones.
4. No introduce acoplamiento entre módulos.

Dos clases llamadas `Address` pueden representar conceptos distintos:

- Dirección del cliente.
- Dirección del comercio.
- Dirección de entrega registrada en un pedido.

No deben compartir automáticamente la misma entidad.

## Comunicación entre bounded contexts

Un módulo no debe importar repositorios, modelos ORM ni entidades internas de otro módulo para modificarlos directamente.

Incorrecto:

```python
from modules.catalog.infrastructure.adapters.driven.django_orm.models import ProductModel
```

Preferir:

- Puerto público del módulo.
- Caso de uso público.
- Servicio de consulta.
- Evento de dominio o integración.
- DTO estable.
- Identificador del recurso.

Ejemplo:

```text
conversation
    ↓ CreateOrderPort
order
    ↓ ProductQueryPort
catalog
```

El módulo `conversation` puede interpretar el mensaje del cliente, pero no debe crear directamente registros de pedidos mediante Django ORM.

## Reglas específicas para IA

La IA pertenece principalmente al módulo `conversation` como adaptador o capacidad de aplicación.

Debe usarse para:

- Detectar intención.
- Extraer información del mensaje.
- Redactar respuestas.
- Clasificar consultas.
- Proponer acciones.
- Mantener contexto conversacional.

No debe decidir por sí sola:

- Precios finales.
- Disponibilidad.
- Validez de cupones.
- Totales.
- Estados de pedidos.
- Reglas de cancelación.
- Costos de envío.
- Permisos.

Esas decisiones deben obtenerse mediante casos de uso de los módulos correspondientes.

Flujo esperado:

```text
Mensaje del cliente
        ↓
conversation
        ↓ interpreta intención
application port
        ↓
order / catalog / config_coupon / client
        ↓ ejecuta reglas deterministas
conversation
        ↓
respuesta al cliente
```

Las respuestas estructuradas de la IA deben validarse antes de ejecutar acciones.

Nunca confiar directamente en identificadores, montos, cantidades o estados generados por el modelo.

