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
| `SUPABASE_URL`                                    | Proyecto Supabase (Auth GoTrue) — identidad del personal           | _(vacío)_                                                   |
| `SUPABASE_ANON_KEY`                               | Clave pública anon del proyecto (login del panel)                 | _(vacío)_                                                   |
| `SUPABASE_JWT_SECRET`                             | Secreto de firma HS256 de los JWT (Dashboard → Settings → API)     | _(vacío)_                                                   |
| `SUPABASE_SERVICE_ROLE_KEY`                       | Solo para el comando `create_staff` (admin API) — nunca en el panel| _(vacío)_                                                   |
| `MERCADOPAGO_ACCESS_TOKEN`                        | Access token global de pagos (fallback cuando el negocio no vinculó su cuenta) | _(vacío)_                                           |
| `MERCADOPAGO_CLIENT_ID` / `MERCADOPAGO_CLIENT_SECRET` | Credenciales de la app de Mercado Pago (para el OAuth “Conecta tu cuenta”) | _(vacío)_                                           |
| `MERCADOPAGO_REDIRECT_URI`                        | URL pública donde MP redirige tras autorizar (callback `/api/mercadopago/callback/`) | _(vacío)_                                           |
| `MERCADOPAGO_RETURN_URI`                          | URL del panel a la que el callback devuelve al admin (`/configuracion/pagos/`) | _(vacío)_                                          |
| `MERCADOPAGO_TOKEN_ENCRYPTION_KEY`                | Clave Fernet opcional para cifrar tokens guardados (si falta, derivada de `DJANGO_SECRET_KEY`) | _(vacío)_                                       |
| `MERCADOPAGO_AUTH_BASE_URL`                       | Base URL de autorización OAuth de MP                                | `https://auth.mercadopago.com`                            |
| `BACKEND_PORT` / `UI_PORT`                        | Puertos publicados por Docker Compose                              | `8000` / `8001`                                             |
| `NGROK_AUTHTOKEN`                                 | Token del agente ngrok (requerido por el servicio `ngrok`)         | _(vacío)_                                                   |
| `NGROK_DOMAIN`                                    | Dominio reservado que el túnel publica hacia `backend:8000`        | `hypsicephalic-decisive-lavette.ngrok-free.dev`             |

## Auth del personal (Supabase)

El login del restaurante (roles **ADMIN / CAJA / COCINA**) usa **Supabase Auth** como
proveedor de identidad (email + contraseña). La API valida el JWT de cada request
(HS256 con `SUPABASE_JWT_SECRET`); el **rol vive en la base propia** (tabla `staff`,
Prisma) y el panel inicia sesión contra GoTrue de forma server-side.

**Bootstrap del proyecto** (una vez):

1. Crear el proyecto en [Supabase Dashboard](https://supabase.com/dashboard) (o vía MCP).
2. Copiar al `.env` los valores de **Settings → API**: `Project URL` → `SUPABASE_URL`,
   `anon public` → `SUPABASE_ANON_KEY`, `JWT Secret` → `SUPABASE_JWT_SECRET`.
3. Aplicar la migración local: `uv run prisma migrate deploy --schema api/shared/infrastructure/prisma/schema.prisma`.

**Alta de personal** — dos caminos:

- **Comando** (recomendado): requiere `SUPABASE_SERVICE_ROLE_KEY` en el `.env`
  (Settings → API → `service_role`):

  ```bash
  cd api && PYTHONPATH=. uv run python manage.py create_staff \
      --email caja@rapidfood.local --name "Caja Uno" --role CASHIER
  # roles: ADMIN | CASHIER | KITCHEN
  ```

- **Manual**: crear el usuario en Authentication → Users, copiar su `UUID` del perfil
  y agregar la fila en la tabla `staff` con `supabase_auth_id`, `email`, `name`, `role`.

> Los clientes finales **no se autentican**: los endpoints públicos (catálogo,
> webhook de MercadoPago, payment links, bot de WhatsApp) quedan `AllowAny`; el resto
> de la API exige JWT de un miembro del personal.

## Setup con Docker (recomendado)

```bash
cp .env.example .env          # ajustar credenciales si hace falta
docker compose up --build
# db      → localhost:5432 (PostgreSQL 16)
# backend → http://127.0.0.1:8000/health/
# ui      → http://127.0.0.1:8001/
# proxy   → sin puerto publicado: rutea /api/ al backend y el resto al ui (entrada del túnel ngrok)
```

En desarrollo, `docker-compose.yml` monta el código fuente en los contenedores; los cambios en
`api/` y `ui/` se reflejan al instante gracias a `runserver` (StatReloader). Rebuild solo si cambian
dependencias de Python o el esquema/engine de Prisma.

- `docker compose up --build` → ambiente full stack.
- Para el stack sin UI: `docker compose up -d db backend`.
- La UI arranca con `RAPIDFOOD_CLIENT=mock`; para consumir la API real:
  `RAPIDFOOD_CLIENT=http docker compose up --build` (ojo: los paths del `HttpRapidfoodClient` son aún un esqueleto).

### Túnel ngrok (webhooks de Mercado Pago)

Mercado Pago no puede alcanzar `localhost`, así que el servicio `ngrok` publica el stack en un
dominio HTTPS reservado para recibir las notificaciones de pago.

1. Reservá el dominio en el dashboard de ngrok y copiá tu authtoken.
2. Agregá al `.env` de la raíz:

   ```bash
   NGROK_AUTHTOKEN=tu_token
   NGROK_DOMAIN=hypsicephalic-decisive-lavette.ngrok-free.dev
   ```

3. Levantá el stack; el túnel y el reverse proxy arrancan solos:

   ```bash
   docker compose up --build
   # proxy → entrada única: /api/ y /health/ al backend, el resto al ui
   # ngrok → https://hypsicephalic-decisive-lavette.ngrok-free.dev (-> proxy:80)
   ```

4. En Mercado Pago → Tus integraciones → tu app → **Webhooks**, configurá:
   - **URL:** `https://hypsicephalic-decisive-lavette.ngrok-free.dev/api/orders/payments/mercadopago/webhook/`
   - **Evento:** solo **Order (Mercado Pago)** (topic `orders`). No marques el resto.
   - Guardá y copiá el secret generado a `MERCADOPAGO_WEBHOOK_SECRET` del `.env`.

> El dominio ngrok entra al servicio `proxy` (nginx), que rutea `/api/` y `/health/` al `backend`
> y todo lo demás al panel `ui`. Así conviven en un único túnel el webhook y los
> `MERCADOPAGO_SUCCESS_URL` / `FAILURE_URL` / `PENDING_URL` (que apuntan a la raíz del dominio).
> La configuración vive en `docker/nginx/default.conf`.

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
