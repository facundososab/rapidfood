"""Login/logout views for the admin panel (Supabase Auth / GoTrue)."""
from __future__ import annotations

import time

from django.shortcuts import redirect, render
from django.views import View

from ..auth import (
    AuthError,
    fetch_staff_profile,
    get_token_expiry,
    login_with_password,
)

# One clear, actionable message per failure mode. Never leaks the raw provider
# error (HTTP codes, upstream text) to the person at the login screen.
_ERROR_MESSAGES = {
    "not_configured": (
        "El inicio de sesión no está disponible: falta configurar el proveedor "
        "de identidad. Avisá al administrador (SUPABASE_URL / SUPABASE_ANON_KEY)."
    ),
    "invalid_credentials": (
        "Email o contraseña incorrectos. Revisalos e intentá de nuevo."
    ),
    "email_not_confirmed": (
        "Tu email todavía no está confirmado. Pedile al administrador que lo confirme."
    ),
    "rate_limited": (
        "Demasiados intentos seguidos. Esperá un momento y volvé a probar."
    ),
    "unreachable": (
        "No pudimos contactar al servicio de inicio de sesión. Revisá tu conexión "
        "e intentá de nuevo."
    ),
    "server_error": (
        "No se pudo iniciar sesión. Revisá tus credenciales e intentá de nuevo."
    ),
}


class LoginView(View):
    def get(self, request):
        access_token = request.session.get("supabase_access_token")
        if access_token:
            expiry = get_token_expiry(access_token)
            refresh_token = request.session.get("supabase_refresh_token")
            # A stale pre-refresh session (expired token, no refresh token) must
            # show the login form instead of bouncing to a crashing dashboard.
            if expiry is not None and expiry <= time.time() and not refresh_token:
                request.session.flush()
                return render(request, "login.html")
            return redirect("dashboard")
        return render(request, "login.html")

    def post(self, request):
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""

        if not email or not password:
            return render(
                request,
                "login.html",
                {"email": email, "error": "Ingresá tu email y contraseña."},
            )

        try:
            token, user_email, refresh_token = login_with_password(email, password)
        except AuthError as exc:
            message = _ERROR_MESSAGES.get(exc.code, _ERROR_MESSAGES["server_error"])
            return render(request, "login.html", {"email": email, "error": message})

        request.session["supabase_access_token"] = token
        request.session["supabase_email"] = user_email
        # Kept so the middleware can renew the access token before it expires.
        if refresh_token:
            request.session["supabase_refresh_token"] = refresh_token

        # Best-effort: enrich the session with the staff profile from the API.
        profile = fetch_staff_profile(token)
        if profile:
            request.session["supabase_staff"] = profile

        return redirect("dashboard")


class LogoutView(View):
    def post(self, request):
        request.session.flush()
        return redirect("login")

    def get(self, request):
        # Visiting /logout/ in the browser must actually sign out; otherwise an
        # expired session survives and bounces back to the dashboard.
        request.session.flush()
        return redirect("login")
