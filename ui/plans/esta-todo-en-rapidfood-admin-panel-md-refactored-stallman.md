# Rapidfood — Panel administrativo (Django Templates + HTMX + Alpine.js + Tailwind)

## Context

Objetivo: **el panel administrativo completo de Rapidfood** descrito en `src/imports/pasted_text/rapidfood-admin-panel.md` (SaaS para restaurantes que gestionan pedidos; algunos generados por un agente conversacional, otros creados manualmente tipo POS).

**Cambio de stack (esta instrucción):** el frontend se implementa con **Django Templates + HTMX + Alpine.js + Tailwind CSS**, NO React/Vite. Django es **solo capa de presentación**: no dueño de lógica de negocio ni persistencia. No se usa Django ORM para las entidades del dominio, no se recrean modelos Prisma, no se toca backend/API/casos de uso/dominio/Prisma/PostgreSQL/reglas.

Arquitectura conceptual:
```
Browser → Django Templates (Tailwind + HTMX + Alpine) → Backend/API existente → Casos de uso/dominio → Prisma → PostgreSQL
```

**Regla dura de datos (del brief, sigue vigente):** `src/imports/pasted_text/schema.txt` (Prisma) es la **única fuente de verdad de datos**. No inventar campos/entidades/estados. No existen: imágenes de producto, variantes, stock, SKU, email/DNI/nacimiento del cliente, dirección propia del cliente, repartidores, tracking, historial de estados, `updatedAt` de Order, origen del pedido, control humano del agente, roles, ni sucursales como entidad. Distinguir **persistido vs. calculado vs. estado visual derivado**, y manejar nulos (`unitPrice`, `totalAmount`, `deliveryType`, `paymentType`, `shippingCost` null en `DRAFT`).

**Fuente de datos en esta entrega (decidida):** capa de servicios con **cliente HTTP hacia el backend existente**, pero con **implementación MOCK en memoria** basada estrictamente en el schema. La implementación debe ser **intercambiable por el cliente HTTP real sin modificar views ni templates** (misma interfaz/DTOs).

El repo actual es un scaffold Node/Vite/React que **no se usa** para esta entrega (los archivos de `src/imports/pasted_text/` y `src/imports/DashboardV1/` quedan solo como referencia de spec y estética). Se crea un proyecto Django nuevo.

## Aesthetic direction (sin cambios respecto al plan anterior)

SaaS operativo, denso, sobrio (Stripe / Linear / Shopify Admin / Vercel). Desktop-first, responsive. Tokens derivados del import "Payrole" (`src/imports/DashboardV1/`), expresados como Tailwind v4 `@theme` en el CSS de entrada:

- Primario azul `#3981f7` (+ `#93bafb`, `#cce1ff`, `#ebf3ff`). Texto `#0a112f` / muted `#585860`,`#70707a`,`#9096a2`. Borde `#e4e4e7`. Superficies `#fafafa`/`#f4f4f5`/blanco. Semánticos para badges (verde `#0aaf60`, ámbar, rojo, gris, azul — un color por familia de estado).
- Radios: cards 16px, controles 12px, pills 100px. Padding card 24px, gap sección 32px.
- **Fonts:** sustitutos Google (TT Hoves/Satoshi son comerciales): **Inter** (UI/cuerpo) + display (Manrope o Space Grotesk) para títulos/números, vía `@import` CSS2 (regla `@import` primero en el CSS de entrada de Tailwind).
- Evitar: exceso de cards, gradientes, glassmorphism, sombras fuertes, gráficos decorativos, look de plantilla genérica. Antes de escribir markup, invocar skill `aesthetic-stance`; `create_make_theme` para art direction de página completa.

## Estructura del proyecto Django

```
manage.py
requirements.txt                # django, requests (o httpx), python-dotenv
config/                         # proyecto Django (settings/urls/wsgi)
  settings.py                   # RAPIDFOOD_CLIENT="mock"|"http", API_BASE_URL, static/templates dirs
  urls.py
panel/                          # ÚNICA app Django (capa de presentación)
  urls.py                       # rutas de las 8 secciones + partials HTMX
  views/                        # views por sección (dashboard, orders, products, ...)
  services/                     # ← capa de servicios intercambiable (NO Django ORM)
    dtos.py                     # dataclasses espejo EXACTO del schema + enums (OrderStatus, etc.)
    client.py                   # RapidfoodClient (Protocol/ABC): interfaz de métodos de lectura/escritura
    mock_client.py              # MockRapidfoodClient: datos en memoria (seed), implementa la interfaz
    http_client.py              # HttpRapidfoodClient: consume API existente (esqueleto listo, mismos métodos/DTOs)
    factory.py                  # get_client() según settings — punto único de swap
    seed.py                     # data mock argentina, SOLO campos del schema, fechas relativas a hoy
  domain/                       # SOLO cálculos de presentación (no reglas de negocio del backend)
    pricing.py                  # current_price(product, now)=Price con max(sinceDate)<=now
    metrics.py                  # facturación (Order.totalAmount) vs cobrado online (Payment APPROVED),
                                #   ticket promedio (excluye DRAFT/CANCELLED), pedidos hoy, series, top productos
    orders.py                   # total_units=sum(line.quantity); grupos por estado (flujo)
    coupons.py                  # estado visual: Vencido/Agotado/Disponible; validación wizard
    clients.py                  # métricas por cliente (#pedidos, total gastado, ticket, último)
  templatetags/
    rapidfood.py                # filtros: money(ARS), datetime, short_id, client_name|"Cliente no identificado"
templates/
  base.html                     # shell: sidebar + navbar + {% block content %}, carga HTMX/Alpine/CSS
  components/                   # sidebar, navbar, breadcrumbs, status_badge, payment_status_badge,
                                #   metric_card, data_table, pagination, empty_state, filter_bar,
                                #   search_input, money, datetime_cell, *_link, order_summary, payment_summary,
                                #   dialog, sheet, dropdown, tabs, tooltip, skeleton, toast, stepper
  dashboard/  orders/  products/  payments/  clients/  coupons/  conversations/  configuration/
      # cada carpeta: index.html + detail.html + partials/ (fragmentos que devuelve HTMX)
static/
  css/tailwind.css              # entrada Tailwind (@import fuentes, @import "tailwindcss", @theme tokens)
  css/app.css                   # salida generada por Tailwind CLI (referenciada en base.html)
  js/                           # htmx.min.js, alpine.min.js (vendored) o CDN
tailwind.config.js / package.json (mínimo)  # solo para el CLI de Tailwind que escanea templates/
```

### Capa de servicios (clave del requisito de intercambiabilidad)

- `dtos.py`: `@dataclass` para cada entidad del schema (Client, Order, OrderLine, Product, Price, Category, Discount, Coupon, AppliedCoupon, Payment, Conversation, Message, BusinessConfiguration, BusinessHours, Address) + `Enum`s (`OrderStatus`, `DeliveryType`, `PaymentType`, `PaymentStatus`, `WeekDay`). `role`/`type`/`channel` como `str` (vocab abierto). Campos opcionales como `Optional[...]`.
- `client.py`: interfaz `RapidfoodClient` (Protocol o ABC) con métodos por caso de uso de la UI: `list_orders(filters, page)`, `get_order(id)`, `update_order_status(id, status)`, `create_order(payload)`, `list_products(...)`, `set_product_availability(id, bool)`, `list_payments(...)`, `get_client(id)`, `validate_coupon(code, subtotal)`, `list_conversations()`, `get_conversation(id)`, `get_business_config()`, etc. Devuelve **DTOs**, nunca dicts ad-hoc.
- `mock_client.py`: implementa la interfaz sobre `seed.py` (estado mutable en memoria: crear pedido/cliente/producto/cupón, cambiar estado). Aplica filtros/paginación/búsqueda en Python.
- `http_client.py`: misma interfaz, mapea a llamadas HTTP a `API_BASE_URL` y parsea JSON→DTOs. Se deja como esqueleto funcional (métodos con las requests y el mapeo), no requiere backend vivo ahora.
- `factory.get_client()`: única función que elige impl según `settings.RAPIDFOOD_CLIENT`. **Views y templates dependen solo de la interfaz y los DTOs** → swap sin tocarlos.

## Patrón de páginas (HTMX + Alpine + templates)

- Cada sección: una view "index" que renderiza `index.html` (extiende `base.html`) con la tabla/lista inicial; y views "partial" que devuelven **solo fragmentos** (`partials/*.html`) para HTMX (`hx-get`/`hx-post` + `hx-target`/`hx-swap`).
- **HTMX** para: filtros, búsqueda, paginación, cambiar estado de pedido, activar/desactivar producto, agregar/±cantidad/eliminar líneas en el pedido manual, aplicar cupón, refrescar tablas, abrir contexto de conversación, submits de formularios, refresco parcial de secciones. Flujo: acción → request HTMX → view → HTML partial → swap.
- **Alpine.js** solo para estado visual local: abrir/cerrar sidebar, dropdowns, modales/sheets, tabs, menús, tooltips, toasts. Sin reglas de negocio.
- **Sin duplicar markup:** `base.html` + `{% include %}` de `components/` + `{% block %}`. Badges, tablas, KPI cards, links cruzados y resúmenes son componentes reutilizables parametrizados.

## Contenido por sección (mismo alcance del prompt anterior — todo se construye)

- **Dashboard** (`dashboard/`): selector temporal (Hoy/7d/30d/rango, vía HTMX). KPIs distinguiendo **Facturación** (`Order.totalAmount`) vs **Cobrado online** (`Payment.amount` status=APPROVED, nunca mezclados); Pedidos de hoy; Ticket promedio (excluye DRAFT/CANCELLED); Activos (PENDING/PAID/CONFIRMED/IN_PREPARATION/READY); Completados (DELIVERED vs PICKED_UP); Cancelados. **Flujo de pedidos** DRAFT→…→READY→DELIVERED/PICKED_UP con CANCELLED aparte. **Ventas en el tiempo** (monto + cantidad por día; por hora en "Hoy") — gráfico SVG server-rendered o librería JS ligera (p.ej. Chart.js/uPlot vendored), sin React. **Productos más vendidos** (`OrderLine.quantity`, `Product.description` como nombre — no inventar `name` —, categoría, unidades, facturación por subtotales). **Pedidos recientes**. **Requiere atención**: solo pedidos PENDING/PAID/CONFIRMED/IN_PREPARATION/READY y pagos PENDING/REJECTED/FAILED/EXPIRED, con link directo. NO inventar demoras/no leídos/conversaciones sin responder.
- **Pedidos** (`orders/`): tabla (ID corto, cliente, fecha, entrega, pago, unidades=sum(quantity), subtotal, descuento, envío, total, estado). Filtros estado/entrega/pago/fecha/cliente + búsqueda ID/nombre/apellido/teléfono (todo HTMX). Badges por cada `OrderStatus` con texto ES manteniendo el enum. **+ Nuevo pedido** prominente. Cambio rápido de estado por fila (HTMX).
- **Detalle de pedido** (`orders/detail.html`): encabezado (ID/estado/createdAt/confirmedAt si existe/estimatedTime si existe/entrega/pago). Cliente (+link o "Cliente no identificado"). Líneas (descripción/categoría/cantidad/unitPrice **null en DRAFT manejado**/descuento línea si existe/subtotal). Resumen económico (subtotal/discount/shippingCost/totalAmount con nulos). Cupón desde **`AppliedCoupon`** (snapshot). Pagos (múltiples + link). Conversación solo si `conversationId`. Dirección solo si `addressId` (street/streetNumber/floor/apartment/city/province/postalCode). **NO timeline ficticia** (solo createdAt y confirmedAt).
- **Nuevo pedido — wizard POS** (`orders/` stepper con Alpine para el paso activo, HTMX para datos): (1) Cliente buscar/crear (solo nombre/apellido/teléfono). (2) Productos: buscador (descripción/categoría/precio actual vía `pricing.current_price`/disponibilidad), solo `available=true`, una línea por producto (`@@unique[orderId,productId]` → aumentar quantity), +/−/eliminar (HTMX). (3) Entrega DELIVERY/PICKUP + `shippingCost` y `minOrder` de `BusinessConfiguration`, validar mínimo. (4) Cupón `couponCode` validado (availableUses/dateOfExpiration/type/amount) mostrando descuento. (5) Pago CASH/ONLINE. (6) Confirmación → `create_order` → redirigir a detalle.
- **Productos** (`products/` + detalle + `configuration`/categorías): tabla (descripción/categoría/precio actual/disponibilidad; opcional unidades vendidas y facturación). Detalle + historial `Price[]` + pedidos donde apareció. Crear/editar solo description/category/available; precio vía registros `Price`. Toggle disponible (HTMX). Categorías: descripción + productos (1 categoría por producto). NO imagen/stock/SKU/variantes/marca.
- **Pagos** (`payments/` + detalle): KPIs por `Payment.status`. Tabla (ID corto/pedido/provider/externalId/amount/status/createdAt/updatedAt). Filtros estado/proveedor/fecha. Detalle con badges + link al pedido.
- **Clientes** (`clients/` + perfil): tabla persistidos (nombre/apellido/teléfono) + derivados (#pedidos/total gastado/ticket/último/#conversaciones). Perfil: info + métricas + `orders` + `conversations`. NO email/nacimiento/notas/tags/dirección personal.
- **Cupones** (`coupons/` + detalle/historial): tabla (código/tipo/monto/usos/vencimiento/estado visual Vencido/Agotado/Disponible — no persistir `active`). Crear: couponCode/type(String)/amount/availableUses/dateOfExpiration. Historial vía `AppliedCoupon`.
- **Conversaciones** (`conversations/`): layout 3 columnas [lista][chat][contexto]. Lista: cliente/canal/último mensaje/fecha (max `Message.createdAt`)/sentimiento/última intención. Sin contador de no leídos. Chat: `Message[]` por createdAt, distinguir por `role` (USER/AGENT/SYSTEM) soportando valores desconocidos. Contexto: cliente/teléfono/canal/sentimiento/intención/pedidos (`Conversation.orders`, abribles). **NO** "Tomar conversación/Pausar IA".
- **Configuración** (`configuration/`): `BusinessConfiguration` (businessName/minOrder/shippingCost/availableZone). Horarios `BusinessHours` por `WeekDay` con openFromHour/openToHour String "HH:MM" (time picker que convierte). Direcciones `BusinessConfiguration.addresses`.

Navegación cruzada real (Pedido↔Cliente/Conversación/Pagos/Cupón/Productos, Pago→Pedido, Producto→Categoría/Pedidos, Cupón→Aplicaciones→Pedidos) vía componentes `*_link`.

## Datos mock (solo campos del schema)

Realista argentino: productos (Hamburguesa Clásica, Doble Bacon, Pizza Napolitana, Muzarella, Papas con Cheddar, Empanada de Carne, Coca-Cola 500 ml), categorías (Hamburguesas/Pizzas/Acompañamientos/Bebidas), clientes (Martina López, Nicolás Fernández, Lucía Romero, Tomás García…), canal WHATSAPP. Pedidos en variados estados con fechas relativas a hoy; `Price[]` con varios `sinceDate`; pedidos sin cliente (null), en DRAFT con `unitPrice`/`totalAmount` null, con `AppliedCoupon`, con múltiples `Payment`. Estado mutable en memoria en `mock_client`.

## Tailwind en Django

Tailwind CSS v4 vía **Tailwind CLI standalone** (o `@tailwindcss/cli` en un `package.json` mínimo) que escanea `templates/**/*.html` y `panel/**` y compila `static/css/tailwind.css` → `static/css/app.css`. `base.html` referencia el CSS compilado y carga HTMX + Alpine (vendored en `static/js/` o CDN). No PostCSS extra.

## Dependencias / setup

- Python: `django`, `requests` (o `httpx`), `python-dotenv`. `requirements.txt`.
- Node (solo build CSS): Tailwind CLI. Script `npm run css` (watch) documentado.
- El scaffold Vite/React del repo no se elimina pero queda sin uso para esta entrega.

## Archivos clave a crear

- Proyecto: `manage.py`, `config/settings.py|urls.py|wsgi.py`, `requirements.txt`.
- App: todo bajo `panel/` (views, `services/`, `domain/`, `templatetags/`) y `templates/`, `static/`.
- CSS entrada `static/css/tailwind.css` + `tailwind.config.js` + `package.json` mínimo.

## Verificación

1. `pip install -r requirements.txt`; compilar CSS con Tailwind CLI; `python manage.py runserver`.
2. Recorrer las 8 secciones desde el sidebar; abrir detalle de pedido/cliente/pago/producto/conversación y comprobar links cruzados.
3. Probar interacciones **HTMX** sin recarga completa: filtrar/buscar/paginar pedidos, cambiar estado de pedido, toggle disponibilidad de producto, y el wizard **+ Nuevo pedido** de punta a punta (crear cliente, agregar mismo producto 2 veces → una línea quantity 2, validar `minOrder`, aplicar cupón, elegir pago) → redirección a detalle con los datos.
4. Casos null: pedido DRAFT sin unitPrice/total no rompe; pedido sin cliente → "Cliente no identificado"; sin conversación/dirección oculta esas secciones.
5. Estados derivados: badge cupón Vencido/Agotado/Disponible; "Requiere atención" solo estados reales; Dashboard separa Facturación vs Cobrado online.
6. **Intercambiabilidad:** cambiar `RAPIDFOOD_CLIENT` de `mock` a `http` no debe requerir tocar views ni templates (solo debe fallar por falta de backend vivo, no por acoplamiento). Verificar que views usan `get_client()` y DTOs, nunca el mock directamente.
7. Alpine solo maneja UI local (sidebar/dropdowns/modales/tabs); sin lógica de negocio en JS.
8. Responsive desktop→tablet→mobile (sidebar colapsable con Alpine, tablas adaptadas).
