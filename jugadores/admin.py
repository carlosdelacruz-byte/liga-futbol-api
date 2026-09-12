from django.contrib import admin

from .models import JugadorModel, PosicionModel


@admin.register(PosicionModel)
class PosicionAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "abreviatura"]
    search_fields = ["nombre", "abreviatura"]


@admin.register(JugadorModel)
class JugadorAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "dorsal",
        "nombres",
        "apellidos",
        "equipo",
        "posicion",
        "activo",
    ]
    list_filter = ["equipo", "posicion", "activo", "nacionalidad"]
    search_fields = ["nombres", "apellidos"]
