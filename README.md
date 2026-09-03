# Rapidfood

Monorepo Python 3.13 gestionado con [uv](https://docs.astral.sh/uv/). Arquitectura hexagonal (Ports & Adapters)
con 5 apps — `client`, `conversation`, `order`, `catalog`, `config_coupon` — y un panel de administración
HTML (HTMX/Tailwind) en `ui/`.

- **Django + DRF** = solo la capa HTTP de entrada (inbound). Cero `django.db.models`.
- **Prisma Client Python** = dueño único del modelo de datos (`schema.prisma`).
  `prisma migrate dev` es la única fuente de verdad de migraciones.
- **PostgreSQL 16**.
- **import-linter** = gate de arquitectura (layers + forbidden + acyclic).
- **pytest + pytest-django** = runner de tests; el fixture de sesión crea `test_<db>` y corre
  `prisma migrate deploy` contra la base de tests.

> **Prerequisito de red**: `uv sync` descarga los binarios del engine de Prisma
> (binaries.prisma.sh). Sin red, el setup falla ahí — es esperado.

## Variables de entorno

Hay **un único `.env` en la raíz del repo** (plantilla: `.env.example`). Lo leen Docker Compose
(interpolación), el CLI de Prisma, Django API (`api/config/settings.py`) y el panel (`ui/config/settings.py`).
Opcionalmente, `api/.env` y `ui/.env` se cargan primero como override local por componente.

| Variable                                          | Definición                                                         | Default                                                     |
| ------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------- |
| `DATABASE_URL`                                    | Conexión a Postgres usada por Prisma (único dueño de los datos)    | `postgresql://rapidfood:rapidfood@localhost:5432/rapidfood` |
| `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` | Credenciales del servicio `db` — solo las usa Docker Compose       | `rapidfood` / `rapidfood` / `rapidfood`                     |
| `POSTGRES_PORT`                                   | Puerto de Postgres (compose)                                       | `5432`                                                      |
| `DJANGO_SECRET_KEY`                               | Clave de firma de Django — cambiarla fuera de dev                  | `dev-only-insecure-key`                                     |
| `DJANGO_DEBUG`                                    | `1` = servidor de desarrollo                                       | `1`                                                         |
| `DJANGO_ALLOWED_HOSTS`                            | Hosts permitidos (separados por coma)                              | `*`                                                         |
| `RAPIDFOOD_CLIENT`                                | Fuente de datos del panel: `mock` (en memoria) u `http` (API real) | `mock`                                                      |
| `RAPIDFOOD_API_BASE_URL`                          | Base URL de la API para el panel con `RAPIDFOOD_CLIENT=http`       | `http://localhost:8000`                                     |
| `RAPIDFOOD_API_TOKEN`                             | Token opcional del panel hacia la API real                         | _(vacío)_                                                   |
| `BACKEND_PORT` / `UI_PORT`                        | Puertos publicados por Docker Compose                              | `8000` / `8001`                                             |

## Setup con Docker (recomendado)

```bash
cp .env.example .env          # ajustar credenciales si hace falta
docker compose up --build
# db      → localhost:5432 (PostgreSQL 16)
# backend → http://127.0.0.1:8000/health/
# ui      → http://127.0.0.1:8001/
```

En desarrollo, `docker-compose.yml` monta el código fuente en los contenedores; los cambios en
`api/` y `ui/` se reflejan al instante gracias a `runserver` (StatReloader). Rebuild solo si cambian
dependencias de Python o el esquema/engine de Prisma.

- `docker compose up --build` → ambiente full stack.
- Para el stack sin UI: `docker compose up -d db backend`.
- La UI arranca con `RAPIDFOOD_CLIENT=mock`; para consumir la API real:
  `RAPIDFOOD_CLIENT=http docker compose up --build` (ojo: los paths del `HttpRapidfoodClient` son aún un esqueleto).

## Setup sin Docker (todo local)

Requiere **PostgreSQL**, **uv** y **Python 3.13**. Solo difieren la instalación/gestión de
Postgres y la activación del venv del panel; los pasos de proyecto son iguales en los 3 OS.

### 1) PostgreSQL — macOS (Homebrew)

```bash
brew install postgresql@16
#    si la fórmula es keg-only, agrega a tu PATH:
#    export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
brew services start postgresql@16

createuser --createdb rapidfood
psql -c "ALTER USER rapidfood WITH PASSWORD 'rapidfood';"
createdb -O rapidfood rapidfood
```

### 1) PostgreSQL — Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable --now postgresql      # o: sudo service postgresql start

sudo -u postgres createuser --createdb rapidfood
sudo -u postgres psql -c "ALTER USER rapidfood WITH PASSWORD 'rapidfood';"
sudo -u postgres createdb -O rapidfood rapidfood
```

> En Ubuntu es normal conectarse con el superusuario `postgres`; hacia `localhost:5432`
> la autenticación es por password, así que las credenciales de arriba alcanzan.

### 1) PostgreSQL — Windows

Instalar PostgreSQL 16 con el instalador EDB (postgresql.org) — arranca el servicio y deja
`psql` en el PATH (alternativa: `choco install postgresql16`). Luego, desde PowerShell:

```powershell
psql -U postgres -c "CREATE USER rapidfood WITH CREATEDB PASSWORD 'rapidfood';"
psql -U postgres -c "CREATE DATABASE rapidfood OWNER rapidfood;"
```

### 2) — 7) Proyecto (común a macOS/Linux)

```bash
# 2) Entorno
cp .env.example .env          # único .env, en la raíz del repo

# 3) Dependencias + motor de Prisma
uv sync
uv run prisma generate --schema api/shared/infrastructure/prisma/schema.prisma

# 4) Migraciones (con la base corriendo)
uv run prisma migrate deploy --schema api/shared/infrastructure/prisma/schema.prisma

# 5) API (desde api/)
cd api
uv run python manage.py runserver        # → http://127.0.0.1:8000/health/

# 6) Panel (desde ui/ — venv aparte)
cd ../ui
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver 8001          # → http://127.0.0.1:8001/
```

> El fixture de tests crea la base `test_rapidfood` automáticamente (requiere que el rol tenga `CREATEDB`).

> Nota: `prisma generate`/`prisma migrate` requieren `--schema`; `prisma generate` solo no encuentra el schema.

## Verificación

```bash
# desde api/ (uv resuelve el proyecto desde la raíz hacia arriba)
uv run python manage.py check                # sanity Django
uv run python manage.py makemigrations --check --dry-run   # no-op (Prisma es dueño del esquema)
uv run python manage.py runserver            # dev server → http://127.0.0.1:8000/health/
uv run pytest                                # incluye smoke test de DB vía Prisma
uv run import-linter lint --config ../pyproject.toml   # contracts de import-linter
```

Reglas de arquitectura (verificadas por import-linter):

- Las apps se comunican entre sí SOLO vía `application/ports` (nunca `adapters/`, `use_cases/`, `domain/`).
- `domain/`, `application/ports/` y `application/use_cases/` NO importan `django`, `rest_framework` ni `prisma`.
- Los adapters HTTP (inbound) nunca tocan adapters outbound directamente.
