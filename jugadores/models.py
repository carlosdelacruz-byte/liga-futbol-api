from django.db import models


class PosicionModel(models.Model):
   nombre = models.CharField(max_length=50, unique=True, null=False)
   abreviatura = models.CharField(max_length=3, unique=True, null=False)
   descripcion = models.TextField(null=True, blank=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      db_table = "posiciones"
      verbose_name = "Posicion"
      verbose_name_plural = "Posiciones"

   def __str__(self):
      return self.nombre


class JugadorModel(models.Model):
   PIE_HABIL = [
      ("derecho", "Derecho"),
      ("izquierdo", "Izquierdo"),
      ("ambidiestro", "Ambidiestro")
   ]

   nombres = models.CharField(max_length=80, null=False)
   apellidos = models.CharField(max_length=80, null=False)
   dorsal = models.IntegerField(null=False)
   fecha_nacimiento = models.DateField(null=False)
   nacionalidad = models.CharField(max_length=60, null=False)
   altura_cm = models.IntegerField(null=True, blank=True)
   pie_habil = models.CharField(max_length=12, choices=PIE_HABIL, default="derecho")
   foto_url = models.TextField(null=True, blank=True)
   activo = models.BooleanField(default=True)
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   equipo = models.ForeignKey('ligas.EquipoModel', on_delete=models.PROTECT, related_name="jugadores")
   posicion = models.ForeignKey(PosicionModel, on_delete=models.PROTECT, related_name="jugadores")

   class Meta:
      db_table = "jugadores"
      unique_together = [["equipo", "dorsal"]]
      verbose_name = "Jugador"
      verbose_name_plural = "Jugadores"

   def __str__(self):
      return f"{self.dorsal} - {self.nombres} {self.apellidos}"
