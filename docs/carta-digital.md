# Carta digital — menú público con link desde WhatsApp

## Qué es

Permite que un cliente pida la carta por WhatsApp y reciba un **link a una página pública** (`/carta/`) con el menú y los **precios en vivo desde la base de datos**. La página es de solo lectura y ofrece un botón para pedir por WhatsApp.

Flujo end-to-end:

1. El cliente escribe al agente pidiendo la carta o el menú.
2. El agente llama a la tool `get_menu_link` (backend) y comparte la URL `<MENU_PUBLIC_BASE_URL>/carta/`.
3. El cliente abre el link en el navegador.
4. La página `/carta/` consulta los dos endpoints públicos y renderiza la carta con los precios actuales.

## Piezas y ubicación

| Pieza | Módulo / capa | Ubicación |
| --- | --- | --- |
| Endpoint público de menú | `catalog` (REST) | `api/modules/catalog/infrastructure/adapters/driver/rest/views.py` (`PublicMenuView`) |
| Caso de uso del menú | `catalog` (application) | `api/modules/catalog/application/use_cases/get_public_menu_use_case.py` |
| Puerto + DTOs públicos del menú | `catalog` (ports) | `api/modules/catalog/application/ports/driver/get_public_menu_ports.py` |
| Endpoint público de contacto | `conversation` (REST) | `api/modules/conversation/infrastructure/adapters/driver/rest/views.py` (`PublicContactView`) |
| Caso de uso de contacto | `conversation` (application) | `api/modules/conversation/application/use_cases/get_public_contact.py` |
| Tool del agente | `conversation` (LangChain) | `api/modules/conversation/infrastructure/adapters/driver/langchain/tools.py` (`get_menu_link`) |
| Prompt del agente | `conversation` (LangChain) | `api/modules/conversation/infrastructure/adapters/driver/langchain/prompt.py` (v2.3.0) |
| Guard de URL de carta | `conversation` (LangChain) | `.../langchain_conversation_agent_adapter.py` (`_guard_menu_links`) |
| Página pública | UI (Django) | `ui/panel/views/menu.py` + `ui/templates/menu/index.html` |
| Service público de la UI | UI (services) | `ui/panel/services/public_menu.py` |

## Endpoints públicos

Ambos son `AllowAny`, read-only, y no exponen secretos ni datos internos.

### `GET /api/catalog/menu/`

Devuelve la carta: categorías → productos **disponibles** → variantes con **precio actual** → grupos de modificadores. Los precios salen en vivo de `ProductVariant` (historial `Price`). `Cache-Control: no-store`.

```json
{
  "categories": [
    {
      "id": "uuid",
      "name": "Hamburguesas",
      "products": [
        {
          "id": "uuid",
          "name": "Hamburguesa Clásica",
          "description": "Pan, carne, queso",
          "image_url": null,
          "variants": [
            { "id": "uuid", "name": "Simple", "price": "5200.00", "available": true }
          ],
          "modifier_groups": [
            {
              "id": "uuid",
              "name": "Agregados",
              "min_selections": 0,
              "max_selections": 3,
              "options": [
                { "id": "uuid", "name": "Bacon", "price_delta": "500.00", "available": true }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

- `price` / `price_delta` son strings decimales (`"5200.00"`) o `null`.
- `image_url` puede ser `null`.
- Los productos sin categoría se agrupan bajo una categoría `"Otros"` al final.

### `GET /api/conversation/public-contact/`

Perfil público del negocio para el encabezado de la carta y el botón de WhatsApp.

```json
{
  "business_name": "Rapidfood Palermo",
  "whatsapp_number": "+54 9 341 353-1060",
  "whatsapp_enabled": true
}
```

- `whatsapp_number` es el `display_phone_number` de la configuración de WhatsApp (nunca el token ni el secreto).
- Si el negocio no tiene configuración de WhatsApp: `whatsapp_number: null`, `whatsapp_enabled: false`.

## Página pública `/carta/`

- **Sin login**: la ruta está en la whitelist de `LoginRequiredMiddleware.PUBLIC_PATHS` (`ui/panel/middleware.py`).
- **Standalone**: no extiende `base.html` (no muestra el chrome del panel); usa `static/css/app.css`.
- **Contenido**: título = `business_name` (o "Nuestra Carta"); categorías → tarjetas de producto (imagen o placeholder, nombre, descripción); variantes con precio formateado (`$ 5.200`), las no disponibles tachadas con "No disponible"; extras con `+$`.
- **CTA**: "Pedir por WhatsApp" → `https://wa.me/<solo dígitos>` cuando hay número.
- **Degradación**: si los endpoints fallan, muestra un estado vacío amigable; nunca rompe la página.
- **Sin caché**: la página lee precios en vivo en cada carga.

## Link desde el agente

- **Tool `get_menu_link`**: devuelve `{"menu_url": "<MENU_PUBLIC_BASE_URL>/carta/"}` y guarda la URL en `turn_state` para el guard. Si no hay base configurada, responde un error de negocio `MENU_LINK_UNAVAILABLE` (nunca un error técnico).
- **Prompt (v2.3.0)**: si el cliente pide la carta o el menú, el agente usa `get_menu_link` y comparte **exactamente** esa URL; nunca la inventa.
- **Guard `_guard_menu_links`**: corre después del guard de pagos y normaliza cualquier URL `/carta` fabricada por el modelo a la canónica (o un mensaje seguro si no hay base). El guard de pagos quedó intacto.

## Configuración

- **`MENU_PUBLIC_BASE_URL`** (variable de entorno): dominio público sobre el que vive `/carta/`.
  - Default: `https://hypsicephalic-decisive-lavette.ngrok-free.dev` (túnel ngrok actual).
  - Declarada en `api/config/settings.py` y en `docker-compose.yml` (servicio `backend`).
  - Para un dominio propio, cambiar solo esta variable; no requiere tocar código.
- **Enrutamiento**: nginx/ngrok mandan `/api/` y `/health/` al backend y **todo el resto a la UI**, así que `<dominio>/carta/` lo sirve la UI.

## Cómo verificar

> `uv` no está instalado en la máquina; se usa el `.venv` del repo.

```powershell
# API (módulos tocados)
.venv\Scripts\python.exe -m pytest api/modules/catalog/tests api/modules/conversation/tests/use_cases -q

# Arquitectura (desde api/)
cd api; & "..\.venv\Scripts\lint-imports.exe" --config ../pyproject.toml

# UI
.venv\Scripts\python.exe -m pytest ui/panel/tests -q
```

Manual: levantar el stack y abrir `<MENU_PUBLIC_BASE_URL>/carta/`.

> Nota de entorno: el comando canónico de Tailwind (`npx @tailwindcss/cli -i static/css/tailwind.css -o static/css/app.css --minify`) requiere un `node_modules`/`package.json` local que el repo no tiene. Si se agrega uno en `ui/`, el build queda reproducible sin instalaciones temporales.

## Cómo migrar a multi-negocio (no implementado)

Hoy el sistema es **single-business** (el negocio se resuelve solo, con fallback `"default"`). Para soportar varios locales:

1. **Identificador público**: agregar un `slug` único y URL-safe a `BusinessConfiguration` (Prisma + dominio + panel). Ej.: `rapidfood-palermo`.
2. **Ruta pública**: `GET /carta/<slug>/` en la UI y `GET /api/catalog/menu/<slug>/` (o `?business=<slug>`) en el backend, resolviendo el `business_config_id` desde el slug.
3. **Scope del menú**: hoy `ListProductsQuery` no filtra por negocio. Agregar `business_config_id` a las queries de catálogo y una columna `business_config_id` en las tablas de producto (migración Prisma), filtrando por negocio.
4. **Contacto por negocio**: `public-contact` resuelve el negocio por slug y devuelve su `WhatsAppConfiguration`.
5. **Link del agente**: el contexto del agente ya trae `business_configuration_id`; `get_menu_link` compone `<MENU_PUBLIC_BASE_URL>/carta/<slug>/` a partir del negocio del contexto (no de un valor global). `MENU_PUBLIC_BASE_URL` sigue siendo el dominio.
6. **Compatibilidad**: mantener `/carta/` con redirect al slug del único negocio, o como default.

## Decisiones y límites (v1)

- **Read-only**: desde la carta no se pide; solo se mira y, si quiere pedir, va a WhatsApp.
- **Single-business**.
- Solo se muestran productos **disponibles**.
- Precios **en vivo**, sin caché.
- El nombre del negocio sale de `BusinessConfiguration.businessName`; no hay logo ni branding rico.

## Archivos clave

- `api/modules/catalog/application/ports/driver/get_public_menu_ports.py`
- `api/modules/catalog/application/use_cases/get_public_menu_use_case.py`
- `api/modules/catalog/infrastructure/adapters/driver/rest/views.py` / `urls.py`
- `api/modules/conversation/application/ports/driver/public_contact_ports.py`
- `api/modules/conversation/application/use_cases/get_public_contact.py`
- `api/modules/conversation/infrastructure/adapters/driver/langchain/tools.py` / `prompt.py` / `langchain_conversation_agent_adapter.py`
- `api/config/settings.py` (`MENU_PUBLIC_BASE_URL`)
- `docker-compose.yml`
- `ui/panel/services/public_menu.py`
- `ui/panel/views/menu.py`, `ui/panel/urls.py`, `ui/panel/middleware.py`
- `ui/templates/menu/index.html`
