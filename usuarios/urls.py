from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
   PerfilView,
   RegistroView,
   UsuarioDetailView,
   UsuarioListCreateView
)

urlpatterns = [
   path("auth/registro/", RegistroView.as_view(), name="registro"),
   path("auth/login/", TokenObtainPairView.as_view(), name="login"),
   path("auth/login/refresh/", TokenRefreshView.as_view(), name="refresh"),
   path("usuarios/perfil/", PerfilView.as_view(), name="usuarios-perfil"),
   path("usuarios/", UsuarioListCreateView.as_view(), name="usuarios-list"),
   path("usuarios/<int:pk>/", UsuarioDetailView.as_view(), name="usuarios-detail"),
]
