from django.contrib import admin

from .models import PartidoModel, ResenaModel


@admin.register(PartidoModel)
class PartidoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "codigo",
        "equipo_local",
        "equipo_visitante",
        "fecha",
        "hora",
        "estado",
        "marcador",
    ]
    list_filter = ["estado", "liga", "jornada", "fecha"]
    search_fields = ["codigo", "equipo_local__nombre", "equipo_visitante__nombre"]
    date_hierarchy = "fecha"


@admin.register(ResenaModel)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ["id", "partido", "autor", "puntuacion", "estado", "created_at"]
    list_filter = ["estado", "puntuacion"]
    search_fields = ["comentario", "autor__username"]
