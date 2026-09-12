"""
Rutas del proyecto LigaApp.

Todo el API cuelga de /api/v1/ y la documentacion de /docs/.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def bienvenida(request):
    """Raiz del sitio: una tarjeta con los puntos de entrada."""
    return JsonResponse(
        {
            "proyecto": "LigaApp API",
            "version": "1.0.0",
            "documentacion": {
                "swagger": "/docs/",
                "redoc": "/redoc/",
                "esquema_openapi": "/schema/",
            },
            "autenticacion": {
                "registro": "/api/v1/auth/registro/",
                "login": "/api/v1/auth/login/",
                "refresh": "/api/v1/auth/login/refresh/",
            },
            "recursos": [
                "/api/v1/ligas/",
                "/api/v1/equipos/",
                "/api/v1/estadios/",
                "/api/v1/posiciones/",
                "/api/v1/jugadores/",
                "/api/v1/usuarios/",
                "/api/v1/partidos/",
                "/api/v1/resenas/",
            ],
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


urlpatterns = [
    path("", bienvenida, name="bienvenida"),
    path("admin/", admin.site.urls),
    # API
    path("api/v1/", include("usuarios.urls")),
    path("api/v1/", include("ligas.urls")),
    path("api/v1/", include("jugadores.urls")),
    path("api/v1/", include("partidos.urls")),
    # Documentacion
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
