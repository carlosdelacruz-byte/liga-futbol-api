from django.db import models

# Dentro del models definimos nuestras tablas


class LigaModel(models.Model):
   # El torneo. Es la cabeza de la jerarquia: una liga agrupa a sus equipos.
   nombre = models.CharField(max_length=100, null=False, blank=False)
   temporada = models.CharField(max_length=9, null=False)
   pais = models.CharField(max_length=60, null=False)
   activa = models.BooleanField(default=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      db_table = "ligas"
      # No puede existir dos veces la misma liga en la misma temporada
      unique_together = [["nombre", "temporada"]]
      verbose_name = "Liga"
      verbose_name_plural = "Ligas"

   def __str__(self):
      # Liga 1 Peru 2025-2026
      return f"{self.nombre} {self.temporada}"


class EquipoModel(models.Model):
   # Un club dentro de una liga
   nombre = models.CharField(max_length=100, null=False, blank=False)
   ciudad = models.CharField(max_length=80, null=False)
   fundacion = models.IntegerField(null=False)
   escudo_url = models.TextField(null=True, blank=True)
   activo = models.BooleanField(default=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   # PROTECT => no se borra una liga que todavia tiene equipos
   liga = models.ForeignKey(LigaModel, on_delete=models.PROTECT, related_name="equipos")

   class Meta:
      db_table = "equipos"
      unique_together = [["liga", "nombre"]]
      verbose_name = "Equipo"
      verbose_name_plural = "Equipos"

   def __str__(self):
      return self.nombre


class EstadioModel(models.Model):
   # La cancha donde juega un equipo. Es el recurso que se reserva.
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
      # Estadio Monumental (Universitario)
      return f"{self.nombre} ({self.equipo.nombre})"
