"""
Configuracion del proyecto LigaApp.

API REST de una liga de futbol: ligas, equipos, estadios, jugadores,
usuarios con JWT y partidos con disponibilidad de estadio.
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las credenciales del archivo .env (nunca se sube al repositorio)
load_dotenv(BASE_DIR / ".env")


def env_bool(clave, por_defecto="False"):
    """Lee una variable de entorno y la interpreta como booleano."""
    return os.environ.get(clave, por_defecto).strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------

# En produccion la clave llega por variable de entorno (Render la genera).
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-solo-para-desarrollo-local")

DEBUG = env_bool("DEBUG", "True")

# Hosts permitidos: en local los de siempre, en Render el que da la plataforma.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com").split(",")
    if host.strip()
]

# Render expone el dominio propio del servicio en esta variable.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    origen.strip()
    for origen in os.environ.get("CSRF_TRUSTED_ORIGINS", "https://*.onrender.com").split(",")
    if origen.strip()
]

# Endurecimiento que solo aplica en produccion. En desarrollo estorbaria:
# forzaria HTTPS en localhost y las cookies dejarian de viajar.
if not DEBUG:
    # Render termina el TLS en su proxy y avisa por esta cabecera.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # un anio
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True


# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Librerias de terceros
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    # Aplicaciones propias (un modulo por dominio)
    "ligas",
    "jugadores",
    "usuarios",
    "partidos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sirve los archivos estaticos en produccion (va justo despues de security)
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# ---------------------------------------------------------------------------
# Base de datos: PostgreSQL
# ---------------------------------------------------------------------------
# La conexion entera viaja en una sola variable, DATABASE_URL. Es el formato
# que entrega Render y evita tener cinco variables sueltas.
#   postgresql://usuario:clave@host:5432/nombre_bd

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        default="postgresql://postgres:postgres@localhost:5432/liga_futbol",
        conn_max_age=600,
        # Render exige SSL; en desarrollo local se desactiva.
        ssl_require=not DEBUG,
    )
}


# ---------------------------------------------------------------------------
# Usuario propio
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "usuarios.UsuarioModel"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Por defecto todo pide login: cada vista abre la puerta a proposito.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ---------------------------------------------------------------------------
# Swagger / OpenAPI
# ---------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "LigaApp API",
    "DESCRIPTION": (
        "API REST de una liga de futbol: ligas, equipos, estadios, jugadores, "
        "usuarios con JWT y programacion de partidos con control de disponibilidad."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True},
    "TAGS": [
        {"name": "auth", "description": "Registro, login y refresco de tokens JWT"},
        {"name": "usuarios", "description": "Gestion de usuarios y perfil propio"},
        {"name": "ligas", "description": "Ligas, equipos y estadios"},
        {"name": "jugadores", "description": "Posiciones y jugadores del plantel"},
        {"name": "partidos", "description": "Fixture, disponibilidad, tabla y resenas"},
    ],
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", "True")


# ---------------------------------------------------------------------------
# Internacionalizacion
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Archivos estaticos (los necesita el admin de Django en Render)
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Correo
# ---------------------------------------------------------------------------
# Sin credenciales SMTP el correo se imprime en la consola: sirve para demostrar
# el envio sin depender de un servidor externo.

EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", "True")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-responder@ligaapp.com")
