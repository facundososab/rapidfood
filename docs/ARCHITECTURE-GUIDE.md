# Guía de Arquitectura - Rapidfood

Esta guía describe los lineamientos arquitectónicos fundamentales del proyecto **Rapidfood**. Está pensada para que cualquier desarrollador (humano o agente de IA) entienda cómo está estructurado el código y cuáles son los límites inquebrantables del diseño.

## 1. Visión General

Rapidfood es una aplicación backend construida en Python (>=3.13). Su característica principal es que utiliza **Django 5 y Django REST Framework (DRF) estrictamente como una capa HTTP (shell)**, mientras que la capa de datos es delegada por completo a **Prisma Client Python**.

Todo el código de negocio está organizado en **Módulos (Bounded Contexts)** completamente aislados que siguen la **Arquitectura Hexagonal (Ports & Adapters)**.

## 2. Stack Tecnológico

- **Gestor de Paquetes:** `uv` (las dependencias viven en `pyproject.toml`, no se usa `requirements.txt`).
- **Framework Web:** Django 5 + DRF. (No se usan vistas de plantillas, sesiones, ni el panel de administración).
- **Capa de Datos:** Prisma Client Python (`schema.prisma` es la única fuente de la verdad para la base de datos).
- **Base de Datos:** PostgreSQL.
- **Testing:** `pytest` con `pytest-django`.
- **Linter de Arquitectura:** `import-linter` (impide ciclos de dependencias y violaciones entre capas).

## 3. Estructura de Módulos (Bounded Contexts)

El backend está dividido en 5 dominios principales, ubicados en `api/modules/`:
1. `client`: Gestión de clientes.
2. `catalog`: Catálogo de productos.
3. `config_coupon`: Configuración y cupones de descuento.
4. `order`: Orquestación de pedidos.
5. `conversation`: Módulo de IA conversacional.

> **Regla de oro:** No existen importaciones circulares entre módulos. Un módulo se comunica con otro **únicamente** a través de sus puertos (interfaces), nunca accediendo directamente a su base de datos o modelos internos.

## 4. Arquitectura Hexagonal (Capas)

Cada módulo dentro de `api/modules/` es un ecosistema cerrado con la siguiente estructura interna, donde las dependencias **siempre apuntan hacia adentro**:

```text
infrastructure  →  application  →  domain
```

### 4.1. Domain (`domain/`)
- **Propósito:** Contiene el corazón del negocio (Entidades, Value Objects, Errores de dominio).
- **Regla estricta:** **Prohibido** importar Django, DRF, Prisma, u otras librerías externas. Solo Python puro.
- **Ejemplo:** `Order`, `OrderItem`, `Money`, `DomainError`.

### 4.2. Application (`application/`)
- **Propósito:** Orquestar la lógica de negocio.
- **Casos de Uso (`use_cases/`):** Clases que ejecutan acciones específicas (ej. `CreateOrderUseCase`).
- **Puertos de Entrada (`ports/driver/`):** Las acciones que el módulo expone hacia afuera (comandos y queries).
- **Puertos de Salida (`ports/driven/`):** Interfaces (Protocolos) de las dependencias que la aplicación necesita para funcionar (ej. `OrderRepositoryPort`), sin importar su implementación tecnológica.

### 4.3. Infrastructure (`infrastructure/`)
- **Propósito:** Implementar los puertos de salida e invocar los puertos de entrada interactuando con el mundo real.
- **Adaptadores Inbound (REST):** Las `views.py` y `serializers.py` de DRF. Analizan el JSON, validan la estructura, e invocan un caso de uso. **No contienen reglas de negocio.**
- **Adaptadores Outbound (Datos):** Repositorios concretos que implementan los puertos utilizando Prisma o Django ORM, adaptando los modelos de base de datos a Entidades puras de dominio. La lógica de traducción entre ORM model y Domain entity **debe vivir en una carpeta `mappers/`** dentro del adaptador (ver sección 8).

### 4.4. Configuration (`configuration/`)
- **Propósito:** El *Composition Root*.
- Aquí es donde se instancian los repositorios concretos y se inyectan en los Casos de Uso. Esto evita que los controladores HTTP (views) o los casos de uso conozcan cómo construir sus dependencias.

## 5. El Rol de Prisma y la Base de Datos

En la mayoría de los proyectos Django, el ORM es el dueño absoluto de la base de datos. En Rapidfood, **el ORM está relegado**.

- **Prisma** es el dueño del esquema (`api/shared/infrastructure/prisma/schema.prisma`).
- Prisma se encarga de crear las tablas y ejecutar las migraciones.
- La configuración de Django para base de datos (`DATABASES`) apunta a una base SQLite en memoria (`:memory:`) que sirve de *placeholder* para que Django pueda arrancar (y correr sus propios tests) sin tocar la base PostgreSQL de producción/desarrollo gestionada por Prisma.

## 6. Linter de Arquitectura

Para asegurar que estas reglas no se rompan por accidente, utilizamos `import-linter`.
Si ejecutás las validaciones, el linter va a abortar con error si detecta que:
- La capa `domain` importa algo de `infrastructure`.
- Una vista HTTP llama directamente a un repositorio de base de datos sin pasar por un caso de uso.
- Hay un ciclo de importación entre los 5 módulos principales.

---
*Para mayor detalle técnico sobre cómo implementar entidades o casos de uso paso a paso, referirse a la skill interna del equipo (`skills/hexagonal-architecture/`).*

## 7. Adaptadores Driver (REST API)

Cuando se implementan vistas (Controladores) en DRF, es **obligatorio** traducir los datos del framework a un objeto puro de Python (`Command` o `Query`) antes de invocar el Caso de Uso. 

Para evitar código repetitivo, la mejor práctica es hacer coincidir los campos del `Serializer` con los del `Command` y usar el desempaquetado de kwargs (`**serializer.validated_data`):

```python
# ✅ CORRECTO: Instanciar usando kwargs (idiomático y limpio)
command = AddLineCommand(
    order_id=order_id,
    **serializer.validated_data
)

# ❌ INCORRECTO: Pasar el diccionario del framework crudo al caso de uso
# container.use_case.execute(serializer.validated_data)
```

## 8. Patrón Mapper en Adaptadores Driven

Todo adaptador driven que use Django ORM **debe** separar la lógica de traducción en una carpeta `mappers/`.

### Estructura obligatoria

```
infrastructure/adapters/driven/
└── django_orm/
    ├── models.py          ← Clases ORM (managed=False, espejo del schema Prisma)
    ├── order_repository.py ← Implementa el puerto; usa el mapper para convertir
    └── mappers/
        ├── __init__.py
        └── order_mapper.py   ← Lógica de traducción ORM ↔ Domain
```

### Responsabilidades de cada archivo

| Archivo | Responsabilidad |
|---|---|
| `models.py` | Define las clases ORM que mapean las tablas de Prisma. Siempre `managed = False`. |
| `mappers/<entity>_mapper.py` | Traduce entre `DjangoModel` y `DomainEntity`. No contiene queries ni lógica de negocio. |
| `<entity>_repository.py` | Ejecuta queries ORM, delega la traducción al mapper, retorna entidades puras. |

### Por qué `models.py` no va dentro de `mappers/`

Django requiere que los modelos sean descubiertos a través del mecanismo de app registry, que convencional­mente espera encontrarlos en `models.py`. Moverlos dentro de `mappers/` no elimina esta necesidad — solo agrega una indirección. `models.py` y `mappers/` tienen responsabilidades distintas y deben permanecer separados.

### Ejemplo de mapper

```python
# mappers/order_mapper.py
from modules.order.domain.models.order import Order
from modules.order.infrastructure.adapters.driven.django_orm.models import OrderModel

class OrderMapper:
    @staticmethod
    def to_domain(model: OrderModel) -> Order:
        return Order(
            id=str(model.id),
            status=OrderState(model.status),
            # ...
        )

    @staticmethod
    def to_orm(order: Order) -> dict:
        return {
            "id": order.id,
            "status": order.status.value,
            # ...
        }
```

### Regla clave

El repositorio es el **único** lugar que interacúa con el ORM. El mapper es el **único** lugar que sabe cómo traducir entre ORM y domain. Nunca mezclar estas dos responsabilidades.
