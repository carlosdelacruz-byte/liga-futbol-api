from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import UsuarioModel


@admin.register(UsuarioModel)
class UsuarioAdmin(UserAdmin):
   list_display = ["id", "username", "email", "rol", "equipo_favorito", "is_active"]
   list_filter = ["rol", "is_active", "is_staff"]
   search_fields = ["username", "email"]
   fieldsets = UserAdmin.fieldsets + (
      ("Datos de LigaApp", {"fields": ("rol", "telefono", "equipo_favorito")}),
   )
   add_fieldsets = UserAdmin.add_fieldsets + (
      ("Datos de LigaApp", {"fields": ("email", "rol", "telefono")}),
   )
