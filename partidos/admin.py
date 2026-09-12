from django.contrib import admin

from .models import PartidoModel, ResenaModel


@admin.register(PartidoModel)
class PartidoAdmin(admin.ModelAdmin):
   list_display = [
      "id", "codigo", "equipo_local", "equipo_visitante",
      "fecha", "hora", "estado"
   ]
   list_filter = ["estado", "liga", "jornada"]
   search_fields = ["codigo"]


@admin.register(ResenaModel)
class ResenaAdmin(admin.ModelAdmin):
   list_display = ["id", "partido", "autor", "puntuacion", "estado"]
   list_filter = ["estado", "puntuacion"]
