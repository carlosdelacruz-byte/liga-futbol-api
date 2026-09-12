from django.db import models


class LigaModel(models.Model):
   nombre = models.CharField(max_length=100, null=False, blank=False)
   temporada = models.CharField(max_length=9, null=False)
   pais = models.CharField(max_length=60, null=False)
   activa = models.BooleanField(default=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      db_table = "ligas"
      unique_together = [["nombre", "temporada"]]
      verbose_name = "Liga"
      verbose_name_plural = "Ligas"

   def __str__(self):
      return f"{self.nombre} {self.temporada}"


class EquipoModel(models.Model):
   nombre = models.CharField(max_length=100, null=False, blank=False)
   ciudad = models.CharField(max_length=80, null=False)
   fundacion = models.IntegerField(null=False)
   escudo_url = models.TextField(null=True, blank=True)
   activo = models.BooleanField(default=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   liga = models.ForeignKey(LigaModel, on_delete=models.PROTECT, related_name="equipos")

   class Meta:
      db_table = "equipos"
      unique_together = [["liga", "nombre"]]
      verbose_name = "Equipo"
      verbose_name_plural = "Equipos"

   def __str__(self):
      return self.nombre


class EstadioModel(models.Model):
   nombre = models.CharField(max_length=120, null=False)
   ciudad = models.CharField(max_length=80, null=False)
   capacidad = models.IntegerField(null=False)
   direccion = models.CharField(max_length=200, null=True, blank=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   equipo = models.ForeignKey(EquipoModel, on_delete=models.PROTECT, related_name="estadios")

   class Meta:
      db_table = "estadios"
      unique_together = [["equipo", "nombre"]]
      verbose_name = "Estadio"
      verbose_name_plural = "Estadios"

   def __str__(self):
      return f"{self.nombre} ({self.equipo.nombre})"
