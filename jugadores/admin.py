from django.contrib import admin

from .models import JugadorModel, PosicionModel


@admin.register(PosicionModel)
class PosicionAdmin(admin.ModelAdmin):
   list_display = ["id", "nombre", "abreviatura"]


@admin.register(JugadorModel)
class JugadorAdmin(admin.ModelAdmin):
   list_display = ["id", "dorsal", "nombres", "apellidos", "equipo", "posicion", "activo"]
   list_filter = ["equipo", "posicion", "activo"]
   search_fields = ["nombres", "apellidos"]
