# Pruebas y Transacciones


La transacción debe definirse alrededor del caso de uso.

Para operaciones locales con Django ORM se puede usar:

```python
from django.db import transaction


class DjangoUnitOfWork:
    def __enter__(self):
        self._context = transaction.atomic()
        self._context.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._context.__exit__(exc_type, exc_value, traceback)
```

No mantener una transacción de base de datos abierta mientras se espera:

- Una respuesta de IA.
- Una API externa.
- Una llamada a WhatsApp.
- Un servicio de geocodificación.
- Una operación lenta de red.

Las operaciones externas no forman parte de la misma transacción de base de datos.

Cuando sea necesario garantizar publicación confiable de eventos, considerar transactional outbox.

## Pruebas

### Domain tests

Ubicación:

```text
tests/domain/
```

Deben probar:

- Invariantes.
- Transiciones de estado.
- Cálculos.
- Value objects.
- Errores de dominio.

No deben usar:

- Django.
- Base de datos.
- HTTP.
- Mocks de infraestructura innecesarios.

### Use case tests

Ubicación:

```text
tests/use_cases/
```

Deben probar casos de uso con:

- Repositorios in-memory.
- Stubs.
- Fakes.
- Mocks de puertos externos.

Ejemplo:

```python
class InMemoryClientRepository:
    def __init__(self) -> None:
        self.clients: dict[str, Client] = {}

    def save(self, client: Client) -> None:
        self.clients[client.id] = client

    def find_by_id(self, client_id: str) -> Client | None:
        return self.clients.get(client_id)

    def find_by_phone(self, phone: str) -> Client | None:
        return next(
            (
                client
                for client in self.clients.values()
                if client.phone.value == phone
            ),
            None,
        )
```

### Integration tests

Ubicación:

```text
tests/integration/
```

Deben probar:

- Repositorios Django ORM.
- Mapeos dominio-persistencia.
- Constraints de base de datos.
- Endpoints REST.
- Configuración y wiring.
- Integraciones reales controladas.

## Convenciones de nombres

Usar nombres orientados al negocio.

Preferir:

```text
register_client_use_case.py
create_order_use_case.py
apply_coupon_use_case.py
client_repository_port.py
django_client_repository.py
```

Evitar:

```text
service.py
manager.py
helper.py
utils.py
common.py
processor.py
```

Un caso de uso debe utilizar verbo más sustantivo:

```text
RegisterClient
CreateOrder
ApplyCoupon
AssignDeliveryAddress
SendConversationMessage
```

Un repositorio debe nombrarse por agregado:

```text
ClientRepositoryPort
OrderRepositoryPort
ConversationRepositoryPort
```

## Tipado

Todo código nuevo debe incluir type hints.

Usar:

- `dataclass` para commands, responses y value objects simples.
- `Protocol` o `ABC` para puertos.
- Tipos explícitos de retorno.
- `Decimal` para dinero.
- `datetime` con zona horaria.
- Enums para estados controlados.

No usar `float` para montos monetarios.

No usar diccionarios sin tipo como contrato principal entre capas.

Incorrecto:

```python
def execute(self, data: dict) -> dict:
    ...
```

Correcto:

```python
def execute(
    self,
    command: CreateOrderCommand,
) -> CreateOrderResponse:
    ...
```

