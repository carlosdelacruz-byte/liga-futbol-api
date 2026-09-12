from django.db import models

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

   goles_local = models.IntegerField(null=True, blank=True)
   goles_visitante = models.IntegerField(null=True, blank=True)

   codigo = models.CharField(max_length=20, blank=True)
   observaciones = models.TextField(null=True, blank=True)

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
      return f"{self.equipo_local.nombre} vs {self.equipo_visitante.nombre} ({self.fecha})"


class ResenaModel(models.Model):
   partido = models.ForeignKey(PartidoModel, on_delete=models.CASCADE, related_name="resenas")
   autor = models.ForeignKey('usuarios.UsuarioModel', on_delete=models.CASCADE, related_name="resenas")
   comentario = models.TextField(null=False)
   puntuacion = models.PositiveSmallIntegerField(default=5)
   estado = models.CharField(max_length=15, choices=ESTADOS_RESENA, default="pendiente")
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)

   class Meta:
      db_table = "resenas"
      unique_together = [["partido", "autor"]]
      verbose_name = "Resena"
      verbose_name_plural = "Resenas"

   def __str__(self):
      return f"Resena de {self.autor.username} - {self.puntuacion}"
