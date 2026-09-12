from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from utils.helpers import EmailHelper

from .models import UsuarioModel
from .permissions import EsAdmin, EsAutorOrAdmin
from .serializers import (
    CambioPasswordSerializer,
    LoginSerializer,
    RegistroSerializer,
    UsuarioSerializer,
)


@extend_schema(tags=["auth"])
class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/ -> access + refresh + datos del usuario."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


@extend_schema(tags=["auth"])
class RegistroView(generics.CreateAPIView):
    """POST /api/v1/auth/registro/ -> crea un usuario con rol hincha."""

    queryset = UsuarioModel.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        usuario = serializer.save()
        EmailHelper.enviar(
            asunto="Bienvenido a LigaApp",
            cuerpo=(
                f"Hola {usuario.username}, tu cuenta fue creada correctamente.\n"
                "Ya podes consultar el fixture y dejar tus resenas."
            ),
            para_email=usuario.email,
        )


@extend_schema_view(
    get=extend_schema(tags=["usuarios"], summary="Listar usuarios (solo admin)"),
    post=extend_schema(tags=["usuarios"], summary="Crear usuario (solo admin)"),
)
class UsuarioListCreateView(generics.ListCreateAPIView):
    """El admin ve el padron completo y puede dar de alta usuarios con rol."""

    queryset = UsuarioModel.objects.select_related("equipo_favorito").all()
    permission_classes = [EsAdmin]
    filterset_fields = ["rol", "is_active", "equipo_favorito"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "date_joined"]

    def get_serializer_class(self):
        # Al crear se piden password y confirmacion; al listar no.
        return RegistroSerializer if self.request.method == "POST" else UsuarioSerializer


@extend_schema_view(
    get=extend_schema(tags=["usuarios"]),
    put=extend_schema(tags=["usuarios"]),
    patch=extend_schema(tags=["usuarios"]),
    delete=extend_schema(tags=["usuarios"], summary="Baja logica del usuario"),
)
class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Cada usuario administra su ficha; el admin administra todas."""

    queryset = UsuarioModel.objects.select_related("equipo_favorito").all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, EsAutorOrAdmin]

    def destroy(self, request, *args, **kwargs):
        """Baja logica: el usuario se desactiva, no se borra."""
        usuario = self.get_object()
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        return Response(
            {"detail": "Usuario desactivado."}, status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(tags=["usuarios"], summary="Perfil del usuario autenticado")
class PerfilView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/usuarios/perfil/ -> el usuario que trae el token."""

    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    tags=["usuarios"],
    summary="Cambiar la contrasena propia",
    request=CambioPasswordSerializer,
    responses={200: None},
)
class CambioPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CambioPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Contrasena actualizada correctamente."})
