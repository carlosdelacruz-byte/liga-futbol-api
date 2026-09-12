from django.db import models

# Los estados por los que pasa un partido.
# La regla de que estado puede ir a cual vive en el serializer.
ESTADOS = [
   ("programado", "Programado"),
   ("jugado", "Jugado"),
   ("suspendido", "Suspendido"),
   ("cancelado", "Cancelado")
]

ESTADOS_RESENA = [
   ("pendiente", "Pendiente"),
   ("publicada", "Publicada"),
   ("oculta", "Oculta")
]


class PartidoModel(models.Model):
   # Un encuentro del fixture. Junta tres dominios: la liga, los equipos
   # y el estadio viven en `ligas`, y el partido los pone a jugar.
   liga = models.ForeignKey('ligas.LigaModel', on_delete=models.PROTECT, related_name="partidos")
   equipo_local = models.ForeignKey(
      'ligas.EquipoModel', on_delete=models.PROTECT, related_name="partidos_de_local"
   )
   equipo_visitante = models.ForeignKey(
      'ligas.EquipoModel', on_delete=models.PROTECT, related_name="partidos_de_visitante"
   )
   estadio = models.ForeignKey('ligas.EstadioModel', on_delete=models.PROTECT, related_name="partidos")

   jornada = models.IntegerField(default=1)
   fecha = models.DateField(null=False)
   hora = models.TimeField(null=False)
   estado = models.CharField(max_length=15, choices=ESTADOS, default="programado")

   # El resultado solo se carga cuando el partido pasa a "jugado"
   goles_local = models.IntegerField(null=True, blank=True)
   goles_visitante = models.IntegerField(null=True, blank=True)

   codigo = models.CharField(max_length=20, blank=True)
   observaciones = models.TextField(null=True, blank=True)

   # Quien programo el partido sale del token, no del body
   programado_por = models.ForeignKey(
      'usuarios.UsuarioModel',
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name="partidos_programados"
   )

   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      db_table = "partidos"
      verbose_name = "Partido"
      verbose_name_plural = "Partidos"

   def __str__(self):
      # Alianza Lima vs Universitario (2026-09-20)
      return f"{self.equipo_local.nombre} vs {self.equipo_visitante.nombre} ({self.fecha})"


class ResenaModel(models.Model):
   # El comentario de un hincha sobre un partido ya jugado
   partido = models.ForeignKey(PartidoModel, on_delete=models.CASCADE, related_name="resenas")
   autor = models.ForeignKey('usuarios.UsuarioModel', on_delete=models.CASCADE, related_name="resenas")
   comentario = models.TextField(null=False)
   puntuacion = models.PositiveSmallIntegerField(default=5)
   estado = models.CharField(max_length=15, choices=ESTADOS_RESENA, default="pendiente")
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      db_table = "resenas"
      # Un hincha opina una sola vez por partido
      unique_together = [["partido", "autor"]]
      verbose_name = "Resena"
      verbose_name_plural = "Resenas"

   def __str__(self):
      return f"Resena de {self.autor.username} - {self.puntuacion}"
