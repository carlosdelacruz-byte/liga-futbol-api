from django.contrib import admin

from .models import EquipoModel, EstadioModel, LigaModel


@admin.register(LigaModel)
class LigaAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "temporada", "pais", "activa"]
    list_filter = ["activa", "pais", "temporada"]
    search_fields = ["nombre", "pais"]


@admin.register(EquipoModel)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "liga", "ciudad", "fundacion", "activo"]
    list_filter = ["liga", "activo", "ciudad"]
    search_fields = ["nombre", "ciudad"]


@admin.register(EstadioModel)
class EstadioAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "equipo", "ciudad", "capacidad"]
    list_filter = ["ciudad"]
    search_fields = ["nombre", "ciudad"]
