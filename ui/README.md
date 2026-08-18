# Rapidfood · Panel administrativo

Capa de presentación construida con **Django Templates + HTMX + Alpine.js + Tailwind CSS**. No usa Django ORM, no define modelos de dominio y consume la interfaz `RapidfoodClient`; actualmente se provee un mock mutable en memoria.

## Puesta en marcha

Requiere Python 3.9 o superior.

```bash
./scripts/bootstrap.sh
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python manage.py runserver
```

Abrí `http://127.0.0.1:8000/`.

Las dependencias se instalan con `pip` a partir de `requirements.txt`; no es necesario versionar ni subir una carpeta `vendor/` al repositorio.

## Estilos

El CSS de producción está en `static/css/app.css`. El archivo fuente Tailwind es `static/css/tailwind.css` y puede compilarse en un entorno que tenga Node.js:

```bash
npx @tailwindcss/cli -i static/css/tailwind.css -o static/css/app.css --minify
```
