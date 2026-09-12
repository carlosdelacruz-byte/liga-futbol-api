import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UsuarioModel


class RegistroSerializer(serializers.ModelSerializer):
    """
    Alta publica de usuarios.

    Nace siempre como `hincha` y sin privilegios: el rol NO se acepta del
    cliente, si no cualquiera se registraria como admin.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirmacion = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        model = UsuarioModel
        fields = [
            "id",
            "username",
            "email",
            "password",
            "password_confirmacion",
            "first_name",
            "last_name",
            "telefono",
            "equipo_favorito",
        ]

    def validate_email(self, value):
        email = value.strip().lower()
        if UsuarioModel.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return email

    def validate_username(self, value):
        if len(value) < 4:
            raise serializers.ValidationError(
                "El nombre de usuario debe tener al menos 4 caracteres."
            )
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise serializers.ValidationError(
                "El nombre de usuario solo admite letras, numeros, punto, guion y guion bajo."
            )
        return value

    def validate_telefono(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("El telefono solo debe contener numeros.")
        if value and len(value) != 9:
            raise serializers.ValidationError("El telefono debe tener 9 digitos.")
        return value

    def validate(self, attrs):
        """Validacion cruzada: compara dos campos entre si."""
        if attrs.get("password") != attrs.get("password_confirmacion"):
            raise serializers.ValidationError(
                {"password_confirmacion": "Las contrasenas no coinciden."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirmacion")
        password = validated_data.pop("password")
        usuario = UsuarioModel(
            **validated_data,
            rol="hincha",
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )
        # set_password hashea la clave. Guardarla plana seria un agujero grave.
        usuario.set_password(password)
        usuario.save()
        return usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """Lectura y edicion de un usuario ya existente."""

    equipo_favorito_nombre = serializers.CharField(
        source="equipo_favorito.nombre", read_only=True, default=None
    )
    rol_display = serializers.CharField(source="get_rol_display", read_only=True)

    class Meta:
        model = UsuarioModel
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telefono",
            "rol",
            "rol_display",
            "equipo_favorito",
            "equipo_favorito_nombre",
            "is_active",
            "date_joined",
        ]
        # El rol solo lo cambia el admin: lo controla la vista, no el cliente.
        read_only_fields = ["username", "date_joined", "is_active"]

    def validate_email(self, value):
        email = value.strip().lower()
        consulta = UsuarioModel.objects.filter(email__iexact=email)
        if self.instance:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return email

    def validate_rol(self, value):
        """Un usuario no se asciende solo: solo el admin cambia roles."""
        request = self.context.get("request")
        if request and self.instance and value != self.instance.rol:
            usuario = request.user
            if not (usuario.rol == "admin" or usuario.is_superuser):
                raise serializers.ValidationError(
                    "Solo el administrador puede cambiar el rol de un usuario."
                )
        return value


class CambioPasswordSerializer(serializers.Serializer):
    """Cambio de contrasena del propio usuario."""

    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(
        write_only=True, min_length=8, validators=[validate_password]
    )

    def validate_password_actual(self, value):
        usuario = self.context["request"].user
        if not usuario.check_password(value):
            raise serializers.ValidationError("La contrasena actual es incorrecta.")
        return value

    def validate(self, attrs):
        if attrs["password_actual"] == attrs["password_nueva"]:
            raise serializers.ValidationError(
                {"password_nueva": "La nueva contrasena debe ser distinta de la actual."}
            )
        return attrs

    def save(self, **kwargs):
        usuario = self.context["request"].user
        usuario.set_password(self.validated_data["password_nueva"])
        usuario.save(update_fields=["password"])
        return usuario


class LoginSerializer(TokenObtainPairSerializer):
    """
    Login de Simple JWT, con los datos del usuario dentro de la respuesta.

    Asi el frontend no tiene que pedir el perfil en una segunda llamada.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Estos claims viajan dentro del JWT.
        token["username"] = user.username
        token["rol"] = user.rol
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["usuario"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "rol": self.user.rol,
        }
        return data
