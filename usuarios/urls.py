from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import (
    CambioPasswordView,
    LoginView,
    PerfilView,
    RegistroView,
    UsuarioDetailView,
    UsuarioListCreateView,
)

urlpatterns = [
    # Autenticacion
    path("auth/registro/", RegistroView.as_view(), name="registro"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/login/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/login/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # CRUD de usuarios
    path("usuarios/", UsuarioListCreateView.as_view(), name="usuarios-list"),
    path("usuarios/perfil/", PerfilView.as_view(), name="usuarios-perfil"),
    path(
        "usuarios/cambiar-password/",
        CambioPasswordView.as_view(),
        name="usuarios-password",
    ),
    path("usuarios/<int:pk>/", UsuarioDetailView.as_view(), name="usuarios-detail"),
]
