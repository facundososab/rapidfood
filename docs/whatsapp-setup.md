# Conectar un número de WhatsApp (WhatsApp Cloud API)

Guía paso a paso para conectar un número a Rapidfood usando la **WhatsApp Cloud API
de Meta**. Cubre la creación de la app, los requisitos del número, las credenciales
(access token, app secret, verify token), la configuración del webhook y la carga
desde el panel. Al final hay una sección de **problemas comunes**.

> Rapidfood guarda **una configuración de WhatsApp por negocio** (`whatsapp_configuration`),
> editable desde el panel (**Configuración → WhatsApp**). Los secretos (`access_token`,
> `app_secret`) se cifran en reposo con Fernet.

---

## 0. Resumen rápido

1. Crear una app en Meta for Developers (tipo **Business**).
2. Agregar un número: **de prueba** (gratis, sin método de pago) o **propio** (requiere que el número **no esté asociado a WhatsApp**).
3. Copiar **Phone number ID**, **WABA ID**, **Access token** y **App secret**.
4. Elegir un **Verify token** (lo inventás vos).
5. Cargar todo en **Configuración → WhatsApp** del panel.
6. En Meta, configurar el **webhook** (Callback URL + Verify token + suscribir `messages`).
7. (Opcional) Crear un **template utility** para confirmar pagos fuera de las 24 h.

---

## 1. Crear la app en Meta

1. Entrá a [developers.facebook.com/apps](https://developers.facebook.com/apps) → **Crear app**.
2. Elegí el caso de uso **Business** → tipo **App de negocios / Business**.
3. Asociá (o creá) un **Portafolio de negocio**.
4. Dentro de la app, andá a **Agregar productos → WhatsApp → Configurar**. Esto crea
   (o asocia) una **WhatsApp Business Account (WABA)**.

> Todo el flujo de WhatsApp vive en el menú izquierdo: **WhatsApp → API Setup** y
> **WhatsApp → Configuration**.

---

## 2. Elegir el número

Tenés dos caminos:

### Opción A — Número de prueba (recomendado para desarrollo)

Meta te da un número de prueba **gratis** (sin método de pago) con hasta **5
destinatarios verificados**. Ideal para probar todo el flujo.

- Está en **API Setup → Paso 1** (el "Desde").
- Para agregar destinatarios: en **API Setup → "Para" (To)** → **Administrar lista
  de números de teléfono** → agregás un número y lo verificás con un código que
  Meta te manda por WhatsApp.
- Los números de prueba de este flujo son gratuitos por **90 días**.

### Opción B — Número propio

Requisitos del número:

- **No puede estar asociado a WhatsApp.** No debe estar activo en la app de WhatsApp
  personal ni en la **WhatsApp Business app**, ni registrado en otra API/WABA.
  - Si el número está en la **WhatsApp Business app**: tenés que **dar de baja la
    cuenta** desde la app (Configuración → Cuenta → Eliminar cuenta). Puede haber un
    **periodo de espera** antes de poder registrarlo en la API.
  - Si el número usa WhatsApp personal, hay que eliminar esa cuenta también.
- Debe **recibir SMS o llamada** para la verificación (sirve un fijo que reciba llamadas).
- Debe cumplir la **política de nombre visible (display name)** de Meta.
- Para pasar a **producción** (escribir a cualquier cliente) Meta exige **verificar el
  negocio** y agregar un **método de pago**.

> En resumen: un número "nuevo" o liberado es lo más simple. El caso típico que falla es
> intentar usar un número que ya está en la WhatsApp Business app.

---

## 3. Obtener las credenciales

En **WhatsApp → API Setup** copiá:

| Dato | Dónde | Para qué |
|---|---|---|
| **Phone number ID** | API Setup ("Identificador del número de teléfono") | Identifica tu número emisor; Rapidfood rutea el webhook por este ID. |
| **WABA ID** | API Setup ("Identificador de la cuenta de WhatsApp Business") | Informativo (referencia de la cuenta). |
| **Access token** | API Setup (token temporal) o System User (permanente) | Se usa para enviar/descargar mensajes. |
| **App secret** | App Settings → Basic → **App Secret** | Valida la firma `X-Hub-Signature-256` de los webhooks. |
| **Verify token** | Lo **inventás vos** | Handshake de suscripción del webhook; debe coincidir con el del panel. |

### Access token: temporal vs. permanente

- **Temporal (API Setup):** dura ~24 h. Sirve para probar. **Se vence seguido.**
- **Permanente (recomendado):** Meta Business Settings → **Usuarios → Usuarios del
  sistema** → crear un System User → **Generar token** con permisos
  `whatsapp_business_messaging` y `whatsapp_business_management`. Elegí ese token.

> El `app secret` y el `access token` se guardan **cifrados** en la base de datos.

---

## 4. Cargar las credenciales en Rapidfood

### 4.1 Clave de cifrado (una sola vez)

Generá una clave Fernet y ponela en el `.env` de la raíz:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

```bash
WHATSAPP_CONFIG_ENCRYPTION_KEY=la_clave_generada
```

> No la cambies después: si rotás la clave, los secretos ya guardados dejan de
> descifrarse y hay que volver a cargarlos. (En desarrollo, si no la seteás, se deriva
> de `DJANGO_SECRET_KEY`.)

### 4.2 Migración + cliente Prisma

```bash
cd api
uv run prisma migrate deploy
uv run prisma generate
```

### 4.3 Panel

Entrá a **Configuración → WhatsApp** y cargá:

- **Phone number ID** (obligatorio)
- **Access token** (obligatorio)
- **App secret** (obligatorio)
- **Verify token** (obligatorio — el mismo que vas a pegar en Meta)
- Phone number / WABA / versión de API (opcionales)
- **Template de pago** (nombre + idioma) — opcional, ver §6

Guardá. El panel muestra un toast de confirmación.

---

## 5. Configurar el webhook en Meta

En **WhatsApp → Configuration → Webhook** → **Editar**:

- **Callback URL:**
  ```
  https://<TU_DOMINIO_PUBLICO>/api/conversation/webhook/whatsapp/
  ```
  Tiene que ser **HTTPS público**. En desarrollo usá el dominio de ngrok del stack
  (ver el README → *Túnel ngrok*).
  - **Ojo:** la URL debe incluir **`/api/conversation/webhook/whatsapp/`**. Si ponés
    solo el dominio, Meta pega en el panel y la verificación falla.
- **Verify token:** el mismo que cargaste en el panel.
- **Verificar y guardar.**

Después: **Administrar** (Manage) el webhook → suscribí el campo **`messages`**.

> Si el webhook está en otra WABA/app, hay que configurarlo y suscribirlo **ahí también**.
> El `phone_number_id` que llega en el webhook debe coincidir con el cargado en el panel.

Probá que el endpoint responde (reemplazá las variables):

```bash
curl -s "https://<TU_DOMINIO_PUBLICO>/api/conversation/webhook/whatsapp/?hub.mode=subscribe&hub.verify_token=<VERIFY_TOKEN>&hub.challenge=TEST123"
# Debe devolver: TEST123
```

---

## 6. Confirmación de pago fuera de la ventana de 24 h

- **Dentro** de las 24 h (el cliente escribió hace poco) se responde con **texto libre**.
- **Fuera** de la ventana, WhatsApp **exige un template aprobado**. Si el pago se
  confirma >24 h después del último mensaje del cliente, hace falta un **template
  utility** aprobado.
- Creá el template en **WhatsApp Manager → Plantillas de mensajes** (categoría
  *Utility*), aprobalo, y cargá su **nombre** e **idioma** en el panel.

---

## 7. Costos (referencia, 2026)

- **Recibir** mensajes del cliente: **gratis**.
- **Descargar** media entrante (audio/imagen): **gratis**.
- **Responder** dentro de la ventana de 24 h: desde el **1-oct-2026** se cobra después
  de **1.000 service messages gratis por número/mes** (tarifa *utility* del país).
- **Templates** (marketing/utility/authentication): se cobran por mensaje.
- **Transcribir audio**: no lo cobra Meta. Es un costo aparte del proveedor STT
  (Gemini/Groq); entra con las claves ya configuradas del agente.

> Para desarrollar sin costo: usá el **número de prueba** de Meta.

---

## 8. Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Meta error 131030: Recipient phone number not in allowed list` | Estás con el **número de prueba** y el destinatario no está en la lista | Agregá el número en **API Setup → "Para" → Administrar lista de números** y verificalo |
| `Meta error 131047: Re-engagement message` | Intentás mandar **texto libre fuera de la ventana de 24 h** | Usá un **template utility** aprobado (y cargalo en el panel) |
| El webhook no llega / no aparece nada en el panel | La **WABA del número no está suscrita** al webhook, o estás escribiendo a otro número | Revisá que la URL + verify token estén cargados y que el campo `messages` esté suscrito **para la WABA correcta** |
| El backend loguea `phone_number_id=...` desconocido | El `phone_number_id` del webhook no coincide con el del panel | Copiá el ID **del número que recibe el mensaje** en **Configuración → WhatsApp** |
| `Webhook signature rejected` / 403 en el POST | El **App secret** cargado no es el de la app que manda el webhook | Cargá el App Secret correcto (App Settings → Basic) |
| La verificación del callback falla en Meta | URL sin el path, o verify token distinto | URL completa `.../api/conversation/webhook/whatsapp/` y mismo verify token en ambos lados |
| `'Prisma' object has no attribute 'whatsappconfiguration'` | El cliente Prisma del contenedor quedó viejo | Regenerá dentro del contenedor (`docker compose exec backend uv run prisma generate ...`) o reconstruí; el entrypoint ya lo regenera al boot |
| Token vencido / 500 en el panel | Access token **temporal** vencido o sesión de Supabase vencida | Usá un token permanente de System User; re-logueate en el panel |
| La respuesta no le llega al cliente | Fallo de entrega (p. ej. 131030) — el mensaje igual queda en el panel | Corregí la causa (lista de prueba / token / WABA) |

> Los fallos de entrega se loguean como **warning** y no rompen el webhook ni el panel;
> la conversación queda registrada.

---

## 9. Referencias de código

- Adaptador de webhook (entrada, autenticación, normalización): `api/modules/conversation/infrastructure/adapters/driver/whatsapp/`
- Autenticador (token + firma HMAC): `.../driven/whatsapp/whatsapp_webhook_authenticator.py`
- Transcripción de audio: `.../driven/whatsapp/whatsapp_inbound_audio_transcriber.py`
- Envío saliente: `.../driven/whatsapp/whatsapp_outbound_message_adapter.py`
- Panel: **Configuración → WhatsApp** (vista en `ui/panel/views/configuration.py`)
