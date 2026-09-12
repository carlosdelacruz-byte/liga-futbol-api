from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from utils.helpers import EmailHelper

from .models import UsuarioModel
from .permissions import EsAdmin
from .serializers import RegistroSerializer, UsuarioSerializer


class RegistroView(generics.CreateAPIView):
   # POST /api/v1/auth/registro/ => crea un usuario con rol hincha
   # AllowAny porque todavia no hay token: es la puerta de entrada
   permission_classes = [AllowAny]
   queryset = UsuarioModel.objects.all()
   serializer_class = RegistroSerializer

   def perform_create(self, serializer):
      usuario = serializer.save()
      EmailHelper.enviar(
         asunto="Bienvenido a LigaApp",
         cuerpo=f"Hola {usuario.username}, tu cuenta fue creada correctamente. "
                f"Ya podes consultar el fixture y dejar tus resenas.",
         para_email=usuario.email
      )


class UsuarioListCreateView(generics.ListCreateAPIView):
   # El admin ve el padron completo y puede dar de alta usuarios
   permission_classes = [EsAdmin]
   queryset = UsuarioModel.objects.all()

   def get_serializer_class(self):
      # Al crear se piden las contrasenas, al listar no
      if self.request.method == "POST":
         return RegistroSerializer
      return UsuarioSerializer


class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
   # Cada usuario administra su ficha, el admin administra todas
   permission_classes = [IsAuthenticated]
   serializer_class = UsuarioSerializer

   def get_queryset(self):
      # Si no sos admin, el queryset solo tiene tu propio usuario:
      # cualquier otro id responde 404 y no podes tocarlo
      if self.request.user.rol == "admin":
         return UsuarioModel.objects.all()
      return UsuarioModel.objects.filter(pk=self.request.user.pk)

   def destroy(self, request, *args, **kwargs):
      # Baja logica: el usuario se desactiva, no se borra
      usuario = self.get_object()
      usuario.is_active = False
      usuario.save()
      return Response(status=204)


class PerfilView(generics.RetrieveUpdateAPIView):
   # GET/PUT/PATCH /api/v1/usuarios/perfil/ => el usuario que trae el token
   permission_classes = [IsAuthenticated]
   serializer_class = UsuarioSerializer

   def get_object(self):
      return self.request.user
