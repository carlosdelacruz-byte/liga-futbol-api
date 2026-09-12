from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UsuarioModel


class RegistroSerializer(serializers.ModelSerializer):
   # password solo entra (write_only): el hash NUNCA sale en el JSON
   password = serializers.CharField(
      write_only=True, min_length=8, validators=[validate_password]
   )
   password_confirmacion = serializers.CharField(write_only=True)

   class Meta:
      model = UsuarioModel
      fields = [
         "id", "username", "email", "password", "password_confirmacion",
         "first_name", "last_name", "telefono", "equipo_favorito"
      ]

   def validate_email(self, value):
      if UsuarioModel.objects.filter(email=value).exists():
         raise serializers.ValidationError("Ya existe un usuario con este email.")
      return value

   def validate_username(self, value):
      if len(value) < 4:
         raise serializers.ValidationError(
            "El nombre de usuario debe tener al menos 4 caracteres."
         )
      return value

   def validate_telefono(self, value):
      if value and not value.isdigit():
         raise serializers.ValidationError("El telefono solo debe contener numeros.")
      if value and len(value) != 9:
         raise serializers.ValidationError("El telefono debe tener 9 digitos.")
      return value

   def validate(self, attrs):
      # Validacion cruzada: compara dos campos entre si
      if attrs.get("password") != attrs.get("password_confirmacion"):
         raise serializers.ValidationError({
            "password_confirmacion": "Las contrasenas no coinciden."
         })
      return attrs

   def create(self, validated_data):
      # Los flags de permisos NO se aceptan del cliente: un usuario
      # registrado siempre nace como hincha y sin privilegios.
      validated_data.pop("password_confirmacion")
      password = validated_data.pop("password")

      usuario = UsuarioModel(
         **validated_data,
         rol="hincha",
         is_staff=False,
         is_superuser=False,
         is_active=True
      )
      # set_password se encarga de hashear la clave.
      # Guardarla en texto plano seria un agujero grave.
      usuario.set_password(password)
      usuario.save()
      return usuario


class UsuarioSerializer(serializers.ModelSerializer):
   # Lectura y edicion de un usuario ya existente
   class Meta:
      model = UsuarioModel
      fields = [
         "id", "username", "email", "first_name", "last_name",
         "telefono", "rol", "equipo_favorito", "is_active", "date_joined"
      ]
      read_only_fields = ["username", "date_joined", "is_active"]

   def validate_email(self, value):
      consulta = UsuarioModel.objects.filter(email=value)
      if self.instance:
         consulta = consulta.exclude(pk=self.instance.pk)
      if consulta.exists():
         raise serializers.ValidationError("Ya existe un usuario con este email.")
      return value

   def validate_rol(self, value):
      # Un usuario no se asciende solo: solo el admin cambia roles
      request = self.context.get("request")
      if request and self.instance and value != self.instance.rol:
         if request.user.rol != "admin":
            raise serializers.ValidationError(
               "Solo el administrador puede cambiar el rol de un usuario."
            )
      return value

   def to_representation(self, instance):
      # En la respuesta devolvemos el nombre del equipo favorito,
      # no solo su id
      data = super().to_representation(instance)
      if instance.equipo_favorito:
         data["equipo_favorito_nombre"] = instance.equipo_favorito.nombre
      else:
         data["equipo_favorito_nombre"] = None
      return data
