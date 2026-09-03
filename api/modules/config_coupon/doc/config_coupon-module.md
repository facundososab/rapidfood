# Módulo `config_coupon` — Implementación e Integración

> Documento de referencia para la implementación del bounded context de **cupones y configuración**.
> Cubre: qué se implementó, la arquitectura del módulo, las reglas de negocio modeladas, los contratos expuestos y — de forma crítica — cómo queda pendiente la integración con la aplicación.

## 1. Estado

| Ítem | Estado |
|------|--------|
| Lógica de dominio | ✅ Implementada y testeada |
| Use cases (application) | ✅ Implementados y testeado |
| Puertos driver/driven | ✅ Implementados |
| Adapter de salida (Prisma) | ✅ Implementado |
| Adapter de entrada (REST/DRF) | ✅ Implementado |
| Tests unitarios (domain + use cases) | ✅ **65 passing** (ver §6) |
| Tests de integración (Prisma real) | 🔲 Requiere base del proyecto resincronizada |
| Enrutado en la app / arranque Django | ✅ Hecho — `api/coupons/` (solo admin) |

**El módulo `api/modules/config_coupon/` está implementado y autocontenido como panel de administración.** La conexión con el módulo `order` y el modelo definitivo de usos de cupones quedan pendientes (ver `docs/coupon-integration-roadmap.md`).

## 2. Reglas de negocio modeladas

Fuente: entrevista con el cliente + `docs/reglas-negocio.md` + `docs/req-funcionales.md`.

| # | Regla | Dónde se implementa |
|---|-------|---------------------|
| RN-01 | Tipos de cupón: `FIXED_AMOUNT` (monto fijo) y `PERCENTAGE` (porcentaje). | `domain/models/coupon_type.py` |
| RN-02 | `PERCENTAGE` **no tiene tope** de descuento. | `domain/models/coupon.py` — `calculate_discount` |
| RN-03 | `FIXED_AMOUNT` **requiere** `min_order_amount`. | `domain/models/coupon.py` — validación en constructor |
| RN-04 | El descuento se aplica sobre el **subtotal** (el envío se suma después). | `validate_coupon_use_case.py` |
| RN-05 | Un cupón por pedido (regla de `order`, no de cupones — no implementada aquí). | Fuera de scope; la consume el módulo `order` |
| RN-06 | `available_uses` es un contador **global** de usos del cupón. | `domain/models/coupon.py` — `consume_use` |
| RN-07 | El consumo se produce en la transición `BORRADOR -> PENDIENTE` del pedido. | `consume_coupon_use_case.py` (lo invoca `order`) |
| RN-08 | Vencimiento al **fin del día** 23:59:59. | `domain/models/coupon.py` — `validate_applicable` |
| RN-09 | Flag administrativo `is_active` (activar/pausar cupón). | `toggle_coupon_status_use_case.py` |

## 3. Estructura del módulo

```
api/modules/config_coupon/
├── domain/
│   ├── errors/coupon_errors.py          # DomainError y subtipos
│   └── models/
│       ├── coupon_type.py               # Enum CouponType (FIXED_AMOUNT | PERCENTAGE)
│       ├── coupon_code.py               # Value object CouponCode (normaliza a mayúsculas)
│       └── coupon.py                    # Entidad Coupon (agregado con invariantes)
├── application/
│   ├── ports/
│   │   ├── driver/coupon_admin_ports.py        # Contratos admin (crear/listar/toggle/get)
│   │   ├── driver/coupon_application_ports.py  # Contratos app (validar/consumir para `order`)
│   │   └── driven/
│   │       ├── coupon_repository_port.py       # Protocol de repositorio
│   │       └── clock_port.py                   # Protocol de reloj (inyectable)
│   └── use_cases/
│       ├── create_coupon_use_case.py
│       ├── validate_coupon_use_case.py
│       ├── consume_coupon_use_case.py
│       ├── toggle_coupon_status_use_case.py
│       ├── list_coupons_use_case.py
│       └── get_coupon_by_code_use_case.py
├── infrastructure/
│   └── adapters/
│       ├── driver/rest/
│       │   ├── serializers.py           # Validación de formato de transporte
│       │   ├── views.py                 # APIView → comandos → use cases
│       │   └── urls.py                  # Rutas que inyectan el container
│       └── driven/prisma/
│           ├── prisma_coupon_repository.py  # Adapter Prisma del repositorio
│           └── system_clock.py              # Reloj real (datetime.now)
├── configuration/
│   ├── apps.py                         # AppConfig Django (name="modules.config_coupon")
│   └── container.py                    # Composition root (get_coupon_container, lru_cache)
└── tests/
    ├── domain/                         # Test de entidad y value objects
    ├── use_cases/                      # Test con fakes de puertos
    └── integration/                    # Test del repository Prisma real (marcados db)
```

### Convenciones de capas (hexagonal)

- **`domain/`**: puro Python, sin imports de Django/DRF/Prisma.
- **`application/ports/`**: `Protocol` (PEP 544) + dataclasses inmutables (`frozen=True, slots=True`) para comandos/queries/respuestas.
- **`application/use_cases/`**: orquestan puertos; lanzan `DomainError`; nunca tocan infraestructura.
- **`infrastructure/adapters/driven/`**: implementan puertos driven (Prisma, clock).
- **`infrastructure/adapters/driver/`**: reciben tráfico externo (DRF), traducen HTTP → comandos, traducen errores de dominio → códigos HTTP. **Sin reglas de negocio.**
- **`configuration/container.py`**: único lugar que instancia dependencias concretas. `@lru_cache(maxsize=1)` para singleton.

## 4. Contratos expuestos (application ports)

### Puertos driver — consumidos por el ADMIN

`application/ports/driver/coupon_admin_ports.py`

- `CreateCouponPort.execute(CreateCouponCommand) -> CreateCouponResponse`
- `ToggleCouponStatusPort.execute(ToggleCouponStatusCommand) -> ToggleCouponStatusResponse`
- `ListCouponsPort.execute(ListCouponsQuery) -> ListCouponsResponse`
- `GetCouponByCodePort.execute(GetCouponByCodeQuery) -> CouponSummary`

### Puertos driver — consumidos por el módulo `order` (cross-module)

`application/ports/driver/coupon_application_ports.py`

- `ValidateCouponPort.execute(ValidateCouponCommand) -> ValidateCouponResponse`
- `ConsumeCouponPort.execute(ConsumeCouponCommand) -> ConsumeCouponResponse`

> ⚠️ El módulo `order` debe consumir cupones **solo a través de estos puertos** (nunca el dominio/adapters directo). El comando `ValidateCouponCommand` recibe `coupon_code` y `subtotal`, y devuelve `discount_amount` para congelar en el snapshot `applied_coupon` del pedido (RN-04). `ConsumeCouponCommand` decrementa el contador global al pasar `BORRADOR -> PENDIENTE` (RN-07).

## 5. Endpoints REST (adaptador driver)

| Método | Ruta | Descripción | Use case |
|--------|------|-------------|----------|
| `POST` | `/coupons/` | Crear cupón (admin) | `create_coupon` |
| `GET` | `/coupons/list/` | Listar todos los cupones | `list_coupons` |
| `GET` | `/coupons/by-code/<code>/` | Consultar por código | `get_coupon_by_code` |
| `PATCH` | `/coupons/<id>/status/` | Activar/desactivar cupón | `toggle_coupon_status` |

> `validate`/`consume` **NO se exponen por REST**: son operaciones internas (vía puertos) que consume `order` in-process.

Las rutas (`urls.py`) inyectan los use cases desde el container vía `as_view(create_coupon=...)`; las views declaran atributos `create_coupon = None` que el container puebla. **Esto mantiene las views sin dependencias directas de implementación.**

## 6. Pruebas

### Unitarias (65 passing) — corren sin base de datos

```
tests/domain/test_coupon_code.py
tests/domain/test_coupon.py
tests/use_cases/test_create_coupon_use_case.py
tests/use_cases/test_validate_coupon_use_case.py
tests/use_cases/test_consume_coupon_use_case.py
tests/use_cases/test_toggle_coupon_status_use_case.py
tests/use_cases/test_list_and_get_coupon_use_cases.py
```

Cubren: invariantes de la entidad, cálculo de descuento, vencimiento 23:59:59, consumo de usos, activación/pausa, listado/consulta, y el flujo validar→consumir.

### Integración (`tests/integration/`) — marcadas `db`, NO corren aún

`test_prisma_coupon_repository.py` ejercita el adapter Prisma real (save/find_by_code/find_by_id/update/list_all). Requiere: base de tests Postgres, `prisma generate` + `prisma migrate deploy`. **No corren en el entorno actual** porque la base del proyecto no está resincronizada (ver §8).

## 7. Cambios de schema (Prisma)

`api/shared/infrastructure/prisma/schema.prisma` — modelo `Coupon`:

```prisma
model Coupon {
  id               String          @id @default(uuid()) @map("coupon_id") @db.Uuid
  couponCode       String          @unique @map("coupon_code")
  type             String          // FIXED_AMOUNT | PERCENTAGE (open vocab)
  amount           Decimal         @db.Decimal(10, 2)
  minOrderAmount   Decimal?        @map("min_order_amount") @db.Decimal(10, 2)
  availableUses    Int             @map("available_uses")
  dateOfExpiration DateTime?       @map("date_of_expiration")
  isActive         Boolean         @default(true) @map("is_active")
  appliedCoupons   AppliedCoupon[]

  @@map("coupon")
}
```

> **IMPORTANTE**: para que el adapter Prisma funcione, hace falta ejecutar `prisma generate` (y `prisma migrate dev`) para regenerar el cliente con los campos `minOrderAmount` e `isActive`. Eso depende del arreglo de la base (ver §8).

## 8. Integración — estado real

> ✅ **El enrutado ya está resuelto**: el repo está resincronizado (`manage.py`, `settings.py` → `modules.*`, `pyproject.toml` → `root_package = "modules"`) y los endpoints admin están enrutados en `api/coupons/`. Lo que queda pendiente (conexión con `order`, modelo de usos por persona, consumo atómico, snapshot `AppliedCoupon`) está documentado en `docs/coupon-integration-roadmap.md`. El contenido que sigue (§8.1/§8.2) describe el repo ANTES de la resincronización y queda como histórico.

### 8.1 Diagnóstico del estado actual

La estructura canónica del repositorio es `api/modules/` (bounded contexts) + `api/shared/` + `api/config/`, pero la configuración base **aún apunta al esquema viejo `apps.*`**:

| Archivo | Estado actual | Problema |
|---------|---------------|----------|
| `api/manage.py` | **Vacío (0 líneas)** | `python manage.py` no arranca |
| `api/config/settings.py` | `INSTALLED_APPS = ["apps.client", ...]` | Esos paquetes no existen → Django falla al importar |
| `pyproject.toml` | `root_package = "apps"`, contracts sobre `apps.*`, `pythonpath = ["."]` | Import-linter no valida la estructura real |
| `api/config/urls.py` | Solo `path("health/", ...)` | Los endpoints del módulo no están enrutados |

### 8.2 Pasos para integrar

1. **Regenerar `api/manage.py`** (está vacío): el scaffold estándar de Django 5 con `DJANGO_SETTINGS_MODULE = "config.settings"`.

2. **Resincronizar `api/config/settings.py`**:
   ```python
   INSTALLED_APPS = [
       "django.contrib.staticfiles",
       "rest_framework",
       "modules.client",
       "modules.conversation",
       "modules.order",
       "modules.catalog",
       "modules.config_coupon.configuration",  # AppConfig name="modules.config_coupon"
   ]
   ```
   (Nota: `apps.py` del módulo usa `name = "modules.config_coupon"`, por lo que debe registrarse como `modules.config_coupon.configuration` — es el `AppConfig`.)

3. **Resincronizar `pyproject.toml`** al esquema `modules/`:
   - `root_package = "modules"` (import-linter)
   - `pythonpath = ["api"]` (pytest) — o ajustar `testpaths` a `api/tests`
   - Reemplazar todos los contracts `apps.*` por `modules.*` y los layers a la estructura hexagonal real (`domain`, `application.ports.driver`, `application.ports.driven`, `application.use_cases`, `infrastructure.adapters.driver`, `infrastructure.adapters.driven`)
   - `DJANGO_SETTINGS_MODULE = "config.settings"` (ya correcto, pero debe estar alcanzable desde el `pythonpath`)

4. **Enrutar los endpoints del módulo** en `api/config/urls.py`:
   ```python
   from django.urls import include, path
   urlpatterns = [
       path("health/", views.health, name="health"),
       path("api/", include("modules.config_coupon.infrastructure.adapters.driver.rest.urls")),
   ]
   ```

5. **Regenerar el cliente Prisma** y migrar:
   ```bash
   uv run prisma generate   # regenera el cliente con minOrderAmount/isActive
   uv run prisma migrate dev
   ```

6. **Correr la suite completa**:
   ```bash
   uv run pytest
   ```
   Esto incluiría los tests de integración del repository (marcados `db`, requieren Postgres arriba).

### 8.3 Verificación final

- `python manage.py check` → sin errores.
- `POST /api/coupons/` crea un cupón; `POST /api/coupons/validate/` valida contra un subtotal; `POST /api/coupons/consume/<code>/` decrementa `available_uses`.
- `uv run import-linter` (o el equivalente del proyecto) sin violaciones de capas.

## 9. Notas para quien continúe

- **No duplicar reglas de negocio en serializers/views**: los serializers solo validan formato; la entidad `Coupon` es la dueña de los invariantes (RN-01 a RN-09).
- **`order` consume cupones vía `coupon_application_ports`**: nunca importar el dominio o adapters de `config_coupon` desde otro módulo; los contratos `ValidateCouponPort`/`ConsumeCouponPort` son el borde.
- **Container es el composition root**: cualquier nueva dependencia se inyecta en `configuration/container.py`, no se instancia en las views.
- **Prisma es el dueño de los datos**: Django ORM no debe tocar la tabla `Coupon`; solo el adapter `prisma_coupon_repository.py`.
