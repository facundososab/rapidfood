# rapidfood-admin-panel

Django presenta la interfaz del panel mediante Templates, HTMX, Alpine.js y Tailwind CSS. No usa Django ORM ni define modelos de dominio: toda interacción pasa por `RapidfoodClient` y DTOs en `panel/services/`.

## Estructura

- `manage.py`, `config/`: arranque y configuración Django.
- `panel/views/`: vistas de presentación.
- `panel/services/`: contrato, DTOs, mock y cliente HTTP intercambiables.
- `templates/`: templates y parciales HTMX.
- `static/css/tailwind.css`, `static/css/app.css`: fuente y salida CSS.
- `src/imports/pasted_text/`: brief y schema de referencia; conservarlos.

## Dependencias

Crear un entorno virtual e instalar con:

```bash
python -m pip install -r requirements.txt
```

No se versiona `vendor/`: las dependencias se resuelven desde `requirements.txt`.

## Estilos

Para recompilar CSS en un entorno con Node.js:

```bash
npx @tailwindcss/cli -i static/css/tailwind.css -o static/css/app.css --minify
```
