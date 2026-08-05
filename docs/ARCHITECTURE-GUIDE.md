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
- **Adaptadores Outbound (Datos):** Repositorios concretos que implementan los puertos utilizando Prisma o Django ORM, adaptando los modelos de base de datos a Entidades puras de dominio.

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
