from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
   PerfilView,
   RegistroView,
   UsuarioDetailView,
   UsuarioListCreateView
)

# El login y el refresh ya vienen resueltos por Simple JWT.
# Lo unico que escribimos a mano es el registro.
urlpatterns = [
   path("auth/registro/", RegistroView.as_view(), name="registro"),
   path("auth/login/", TokenObtainPairView.as_view(), name="login"),
   path("auth/login/refresh/", TokenRefreshView.as_view(), name="refresh"),
   # La ruta fija va ANTES de la que captura un <int:pk>,
   # si no "perfil" se interpretaria como el id de un usuario
   path("usuarios/perfil/", PerfilView.as_view(), name="usuarios-perfil"),
   path("usuarios/", UsuarioListCreateView.as_view(), name="usuarios-list"),
   path("usuarios/<int:pk>/", UsuarioDetailView.as_view(), name="usuarios-detail"),
]
