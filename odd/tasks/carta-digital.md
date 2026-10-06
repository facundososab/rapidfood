# Feature: Carta digital (menú público con link desde WhatsApp)

Branch: `Implementacion-Carta`
Estado: en progreso
Forecast: ~900–1100 líneas autoradas (API + UI + tests + docs). Estrategia de entrega: work-unit commits en esta rama única (sin chaining de PR; el PR lo decide el usuario).

## Objetivo

Que un cliente pueda ver la carta del negocio desde un link que el agente de WhatsApp le comparte cuando la pide, con los precios tomados en vivo de la base de datos.

## Problema / por qué

Hoy no existe ninguna superficie pública de menú: el panel está detrás de login y el backend es staff-only. El agente puede leer el menú (`search_products`) pero no puede darle al cliente una página para verlo. La carta debe reflejar siempre el precio actual (vive en `ProductVariant` vía historial de `Price`).

## Alcance

Incluye:
- Endpoint público read-only `GET /api/catalog/menu/` con categorías → productos disponibles (nombre, descripción, imagen) → variantes con precio actual → grupos de modificadores con opciones y precio.
- Endpoint público `GET /api/conversation/public-contact/` con nombre del negocio + número de WhatsApp (para el CTA y el encabezado de la carta).
- Página pública `GET /carta/` en la UI (sin login), con CTA "Pedir por WhatsApp".
- Tool `get_menu_link` del agente + regla de prompt + guard de URL, con base URL configurable (`MENU_PUBLIC_BASE_URL`, default dominio ngrok actual).
- Documentación del feature y de cómo migrarlo a multi-negocio.

Fuera de alcance (v1):
- Pedido desde la carta (la carta es read-only).
- Multi-negocio real (se documenta el camino, no se implementa).
- Nombre/logo configurable como branding rico (se usa el `businessName` existente).

## Restricciones

- Arquitectura hexagonal + import-linter:
  - `catalog` NO puede importar `conversation` (por eso el contacto va en `conversation` y el menú en `catalog`).
  - `conversation` SÍ puede importar `business` y (whitelisted) `catalog.application.ports`.
  - Dominio/aplicación sin Django/DRF/Prisma.
- DRF es staff-only por defecto → los endpoints públicos usan `permission_classes = [AllowAny]` y `authentication_classes = []`.
- La UI pública NO extiende `base.html` (shell del panel). Modelo: `login.html` (standalone, usa `static/css/app.css`).
- Tailwind está compilado (`ui/static/css/app.css`): recompilar con `npx @tailwindcss/cli` si se agregan clases.
- El secreto de WhatsApp (`accessToken`, `appSecret`) está cifrado; `display_phone_number` es plano y es lo único que se expone.

## Tareas

### T1 — Endpoint público de menú (catalog) ✅ commit `a943073`
- [x] `application/ports/driver/get_public_menu_ports.py`: DTOs públicos (`PublicMenu`, `PublicCategory`, `PublicProduct`, `PublicVariant`, `PublicModifierGroup`, `PublicModifierOption`) + protocolo `GetPublicMenuPort`.
- [ ] `application/use_cases/get_public_menu_use_case.py`: arma el árbol desde `list_categories`, `list_products` (solo `state == available`) y `product_query.find_product` (variantes con `price`, modificadores). Productos sin categoría → grupo "Otros" al final si existe.
- [ ] Wiring en `catalog/configuration/container.py` (`get_public_menu`).
- [ ] `infrastructure/adapters/driver/rest/views.py`: `PublicMenuView(APIView)` con `permission_classes=[AllowAny]`, `authentication_classes=[]`, GET, `Cache-Control: no-store`.
- [ ] `.../rest/urls.py`: `path("menu/", ...)`.
- [ ] Tests: use case + REST adapter (anónimo 200, forma de datos).

### T2 — Endpoint público de contacto (conversation)
- [ ] `application/ports/driver/public_contact_ports.py`: DTO `PublicContactView` (`business_name`, `whatsapp_number`, `whatsapp_enabled`).
- [ ] Extender `application/ports/driven/business_service.py` + adapter con `get_name(business_configuration_id)`.
- [ ] `application/use_cases/get_public_contact.py`: nombre vía business_service + número vía `whatsapp_config_repository` (display_phone_number, is_active). Nunca filtra secretos.
- [ ] Wiring en `conversation/configuration/container.py` (`get_public_contact_use_case`).
- [ ] `.../driver/rest/views.py`: `PublicContactView(APIView)` `AllowAny`; `.../rest/urls.py`: `path("public-contact/", ...)`.
- [ ] Tests: use case + REST adapter anónimo.

### T3 — Link de carta desde el agente
- [ ] `api/config/settings.py`: `MENU_PUBLIC_BASE_URL` (default `https://hypsicephalic-decisive-lavette.ngrok-free.dev`).
- [ ] `conversation/configuration/container.py`: campo `menu_public_url` en `ConversationContainer` + parámetro en `build_container`.
- [ ] `api/composition/container.py`: pasar `menu_public_url=settings.MENU_PUBLIC_BASE_URL`.
- [ ] `docker-compose.yml`: env `MENU_PUBLIC_BASE_URL` en `backend`.
- [ ] `langchain/tools.py`: tool `get_menu_link` → `{menu_url: "<base>/carta/"}`, guarda `turn_state["menu_url"]`.
- [ ] `langchain/prompt.py`: bump de versión + sección CARTA (usar `get_menu_link`, nunca inventar URL).
- [ ] `langchain_conversation_agent_adapter.py`: `_guard_menu_links` (normaliza URLs `/carta` a la canónica) aplicado después del guard de pagos.
- [ ] Tests: tool + guard.

### T4 — Página pública `/carta/` (UI)
- [ ] `panel/services/client.py`: `get_public_menu()` + `get_public_contact()` abstractos.
- [ ] `panel/services/http_client.py`: impl con requests SIN auth (sesión nueva, no la compartida) a los endpoints públicos.
- [ ] `panel/services/mock_client.py`: impl desde `seed` (para dev/tests).
- [ ] `panel/views/menu.py`: vista `carta` que arma contexto (menú + contacto + `wa.me`).
- [ ] `panel/urls.py`: `path("carta/", menu.carta, name="menu")`.
- [ ] `panel/middleware.py`: whitelist `/carta/` en `PUBLIC_PATHS`.
- [ ] `ui/templates/menu/index.html`: página standalone, responsive, categorías/productos/variantes/extras, CTA WhatsApp.
- [ ] Recompilar Tailwind (`app.css`).
- [ ] Test: `/carta/` anónimo 200 + contenido.

### T5 — Documentación
- [ ] `docs/carta-digital.md`: cómo funciona, endpoint, env var, y guía para pasar a multi-negocio (slug + ruta `/carta/<slug>` + scope por business).

## Criterios de aceptación

- Un cliente sin login abre `/carta/` y ve categorías, productos disponibles con precio por variante y extras con precio.
- Los precios mostrados provienen de la DB (cambio de precio en el panel → se refleja al recargar).
- El agente, al pedirle la carta, responde con el link configurado (no inventado).
- La carta incluye un botón que abre WhatsApp del negocio.
- `import-linter` pasa; los endpoints públicos son anónimos; los internos siguen protegidos.

## Checks

- API: `uv run pytest` (settings `config.settings`, desde `api/` o raíz).
- Arquitectura: `uv run import-linter lint --config ../pyproject.toml` (desde `api/`).
- UI: pytest de `ui/` en su entorno.
- Manual: levantar stack y abrir `<MENU_PUBLIC_BASE_URL>/carta/`.

## Progreso / evidencia

- [x] T1 — commit `a943073`. `pytest api/modules/catalog/tests` → 26 passed. `lint-imports` → 10 kept, 0 broken. Test del view usa `APIRequestFactory` (ver Notas de entorno).
- [ ] T2
- [x] T3 — `get_menu_link` + prompt 2.3.0 + `_guard_menu_links` + `MENU_PUBLIC_BASE_URL`. Tests: 60 passed (tools/agent/policy). import-linter 10/10. Cambios aditivos: se actualizaron las 2 aserciones de inventario de tools (17→18). Pendiente de commit.
- [ ] T4
- [ ] T5

## Notas de entorno (gotchas descubiertos)

- El `.venv` local estaba incompleto (faltaban PyJWT, requests, shapely, openrouteservice, cryptography, langchain*, mercadopago, psycopg, import-linter). Se instalaron. Runner: `.venv\Scripts\python.exe -m pytest` (uv NO está instalado). Gate: `.venv\Scripts\lint-imports.exe --config ../pyproject.toml` desde `api/`.
- Defecto preexistente: `api/modules/delivery/infrastructure/adapters/driver/rest/urls.py:19` construye `get_delivery_container()` a nivel módulo y `DeliveryContainer.__init__` accede a `db.client`, abriendo Prisma al importar el URLconf. Por eso `django.test.Client`/`resolve` cuelgan sin engine+DB. Los tests de views de API deben usar `APIRequestFactory` (no cargan URLconf). No se toca `delivery` en este sprint (fuera de alcance).

## Próximo paso

Implementar T2 (endpoint público de contacto en conversation).
