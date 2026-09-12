from django.contrib.auth.models import AbstractUser
from django.db import models

from utils.helpers import ROLES


class UsuarioModel(AbstractUser):
   email = models.EmailField(unique=True)
   rol = models.CharField(max_length=15, choices=ROLES, default="hincha")
   telefono = models.CharField(max_length=9, null=True, blank=True)
   equipo_favorito = models.ForeignKey(
      'ligas.EquipoModel',
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name="hinchas"
   )
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      db_table = "usuarios"
      verbose_name = "Usuario"
      verbose_name_plural = "Usuarios"

   def __str__(self):
      return self.username
