---
name: django-hexagonal-modular-architecture
description: Guía para crear, modificar y revisar módulos Django organizados como bounded contexts con arquitectura hexagonal. Usar cuando se implementen entidades, value objects, casos de uso, puertos, adaptadores REST, repositorios Django ORM, configuración, migraciones o pruebas dentro de api/modules.
license: MIT
metadata:
author: project-team
version: '1.0'
scope: [api]
auto_invoke:
  - 'Implementing a Django module'
  - 'Creating a use case'
  - 'Adding a REST endpoint'
  - 'Creating a repository'
  - 'Modifying domain logic'
  - 'Reviewing hexagonal architecture'
---

---

# Django Hexagonal Modular Architecture

Esta skill guía el desarrollo de un backend Django modular basado en arquitectura hexagonal.

El sistema está dividido en bounded contexts independientes:

```text
api/modules/
├── client/
├── catalog/
├── config_coupon/
├── order/
└── conversation/
```

Cada módulo debe mantener sus propias reglas de negocio, casos de uso, puertos, adaptadores, migraciones y pruebas.

## Objetivo

Mantener una arquitectura donde:

- El dominio no dependa de Django.
- Los casos de uso no dependan de HTTP, Django ORM ni frameworks externos.
- Los adaptadores implementen los puertos definidos por las capas internas.
- Cada bounded context sea independiente.
- Las dependencias siempre apunten hacia el dominio.
- La IA interactúe con el negocio mediante casos de uso y no mediante acceso directo a la base de datos.

## References

- Detailed layer rules: [Layer Rules](references/01_layer_rules.md)
- Testing & Transactions: [Testing](references/02_testing_and_transactions.md)

## Estructura de cada módulo

Cada bounded context debe seguir esta estructura:

```text
module/
├── domain/
│   ├── errors/
│   ├── models/
│   └── ports/
├── application/
│   ├── ports/
│   │   ├── driver/
│   │   └── driven/
│   └── use_cases/
├── infrastructure/
│   └── adapters/
│       ├── driver/
│       │   └── rest/
│       └── driven/
│           └── django_orm/
├── configuration/
├── migrations/
└── tests/
    ├── domain/
    ├── use_cases/
    └── integration/
```

## Dirección de dependencias

La dirección permitida es:

```text
infrastructure
      ↓
application
      ↓
domain
```

También:

```text
configuration
      ↓
infrastructure
      ↓
application
      ↓
domain
```

Nunca se permite:

```text
domain → application
domain → infrastructure
domain → Django
application → infrastructure
application → Django ORM
```

## Flujo para implementar una funcionalidad

Antes de escribir código:

1. Identificar el bounded context responsable.
2. Definir la regla de negocio.
3. Identificar el agregado afectado.
4. Crear o modificar entidades y value objects.
5. Definir errores de dominio.
6. Definir el driver port.
7. Definir los driven ports necesarios.
8. Implementar el caso de uso.
9. Crear adaptadores concretos.
10. Registrar dependencias en el container.
11. Exponer la funcionalidad por REST si corresponde.
12. Agregar pruebas de dominio, aplicación e integración.

Orden recomendado:

```text
domain
→ application ports
→ use case
→ tests del use case
→ infrastructure
→ configuration
→ REST
→ integration tests
```

## Lista de verificación

Antes de finalizar una implementación, verificar:

- El dominio no importa Django.
- La aplicación no importa infraestructura.
- Las views no contienen reglas de negocio.
- Los serializers no reemplazan validaciones de dominio.
- Los repositorios devuelven entidades y no modelos ORM.
- Las dependencias se reciben por constructor.
- La configuración concreta está centralizada en `container.py`.
- Las excepciones de dominio se traducen en el borde.
- Los commands no contienen objetos HTTP.
- Los montos usan `Decimal`.
- Los estados usan enums.
- El bounded context propietario de la regla es quien la implementa.
- La IA no modifica directamente datos de negocio.
- Existen pruebas para reglas y casos de uso.
- No se agregó código a `shared` sin justificar que el concepto es realmente común.

## Antipatrones prohibidos

No implementar:

### Active Record como dominio

```python
order = OrderModel.objects.get(id=order_id)
order.status = "confirmed"
order.save()
```

La transición debe pasar por una entidad o comportamiento de dominio.

### Views con reglas de negocio

```python
if order.total > 10000:
    order.discount = 0.1
```

La regla debe estar en el dominio o en una política de negocio.

### Casos de uso dependientes del ORM

```python
from django.db.models import QuerySet
```

La aplicación debe depender de puertos propios.

### Acceso cruzado a tablas de otro módulo

```python
from modules.client.infrastructure.adapters.driven.django_orm.models import ClientModel
```

Usar contratos públicos entre bounded contexts.

### Servicios genéricos

Evitar clases que concentren responsabilidades sin un límite claro:

```text
OrderService
ClientManager
GeneralProcessor
CommonService
```

Preferir casos de uso específicos.

### Entidades anémicas

No crear entidades que sean solamente contenedores de datos cuando existen reglas asociadas.

Incorrecto:

```python
@dataclass
class Coupon:
    percentage: int
    expiration_date: datetime
```

Preferir:

```python
@dataclass
class Coupon:
    percentage: int
    expiration_date: datetime

    def calculate_discount(
        self,
        subtotal: Decimal,
        current_time: datetime,
    ) -> Decimal:
        if current_time >= self.expiration_date:
            raise ExpiredCouponError()

        return subtotal * Decimal(self.percentage) / Decimal("100")
```

## Conducta del agente

Al modificar el proyecto:

1. Inspeccionar primero la estructura y los contratos existentes.
2. Respetar los nombres y convenciones ya utilizadas.
3. No mover reglas entre bounded contexts sin una razón explícita.
4. No crear dependencias desde capas internas hacia infraestructura.
5. Reutilizar puertos existentes cuando representen la misma necesidad.
6. No crear abstracciones prematuras.
7. No agregar archivos genéricos si existe un nombre de negocio más preciso.
8. Mantener los cambios enfocados en la funcionalidad solicitada.
9. Agregar o actualizar pruebas relevantes.
10. Informar cualquier violación arquitectónica detectada.
11. No ocultar deuda técnica con adaptadores temporales sin documentarla.
12. No importar modelos Django desde casos de uso o dominio.

Cuando una solicitud contradiga estas reglas, preservar la dirección de dependencias y proponer la alternativa compatible con arquitectura hexagonal.
