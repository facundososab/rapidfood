# Rapidfood

Monorepo Python 3.13 gestionado con [uv](https://docs.astral.sh/uv/). Arquitectura hexagonal (Ports & Adapters)
con 5 apps: `client`, `conversation`, `order`, `catalog`, `config_coupon`.

- **Django 5 + DRF** = solo la capa HTTP de entrada (inbound). Cero `django.db.models`.
- **Prisma Client Python** = dueño único del modelo de datos (15 entidades, `schema.prisma`).
  `prisma migrate dev` es la única fuente de verdad de migraciones.
- **PostgreSQL 16** vía Docker Compose.
- **import-linter** = gate de arquitectura (layers + forbidden + acyclic).
- **pytest + pytest-django** = runner de tests; el fixture de sesión crea `test_<db>` y corre
  `prisma migrate deploy` contra la base de tests.

> **Prerequisito de red**: `uv sync` descarga los binarios del engine de Prisma
> (binaries.prisma.sh). Sin red, el setup falla ahí — es esperado.

## Setup

```bash
# 1) Entorno
cp .env.example .env          # ajustar credenciales si hace falta

# 2) Base de datos (Postgres 16 en Docker)
docker compose up -d db       # esperar a que el healthcheck pase

# 3) Dependencias (instala deps + binarios del engine de Prisma)
uv sync

# 4) Cliente Prisma tipado
uv run prisma generate

# 5) Primera migración (crea + aplica `migrations/<ts>_init/`)
uv run prisma migrate dev --name init
#    en entornos que ya tienen la migración commiteada: `uv run prisma migrate deploy`
```

## Verificación

```bash
uv run python manage.py check                # sanity Django
uv run python manage.py makemigrations --check --dry-run   # debe ser no-op (Prisma es dueño del esquema)
uv run python manage.py runserver            # dev server → http://127.0.0.1:8000/health/
uv run pytest                                # incluye smoke test de DB vía Prisma
uv run lint-imports                          # contracts de import-linter verdes
```

## Estructura

```
rapidfood/
├── config/                 # shell Django: settings, urls (/health), wsgi/asgi, db.py (singleton Prisma)
├── apps/{client,conversation,order,catalog,config_coupon}/
│   ├── domain/             # entidades puras (sin imports de frameworks)
│   ├── application/ports/{inbound,outbound}/   # Protocolos + DTOs (contratos)
│   ├── application/use_cases/                  # orquestación pura
│   ├── adapters/{inbound/http,outbound/prisma}/# adaptadores de borde
│   └── composition/        # wiring root (container.py)
├── schema.prisma           # fuente de verdad del modelo de datos (15 entidades)
├── migrations/             # migraciones commiteadas (schema en la raíz → CLI usa ./migrations)
└── tests/                  # conftest (test DB + migrate deploy) + smoke tests
```

Reglas de arquitectura (verificadas por `uv run lint-imports`):

- Las apps se comunican entre sí SOLO vía `application/ports` (nunca `adapters/`, `use_cases/`, `domain/`).
- `domain/`, `application/ports/` y `application/use_cases/` NO importan `django`, `rest_framework` ni `prisma`.
- Los adapters HTTP (inbound) nunca tocan adapters outbound directamente.
