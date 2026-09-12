from django.db import models

# Los estados por los que pasa un partido. La regla vive en el serializer:
# de "programado" se avanza, pero nunca se vuelve atras.
ESTADOS_PARTIDO = [
    ("programado", "Programado"),
    ("jugado", "Jugado"),
    ("suspendido", "Suspendido"),
    ("cancelado", "Cancelado"),
]

ESTADOS_RESENA = [
    ("pendiente", "Pendiente"),
    ("publicada", "Publicada"),
    ("oculta", "Oculta"),
]


class PartidoModel(models.Model):
    """
    Un encuentro del fixture.

    Junta tres dominios: la liga y los equipos viven en `ligas`, el estadio
    tambien, y el partido es lo que los pone a jugar en una fecha y hora.
    """

    liga = models.ForeignKey(
        "ligas.LigaModel", on_delete=models.PROTECT, related_name="partidos"
    )
    equipo_local = models.ForeignKey(
        "ligas.EquipoModel", on_delete=models.PROTECT, related_name="partidos_de_local"
    )
    equipo_visitante = models.ForeignKey(
        "ligas.EquipoModel",
        on_delete=models.PROTECT,
        related_name="partidos_de_visitante",
    )
    estadio = models.ForeignKey(
        "ligas.EstadioModel", on_delete=models.PROTECT, related_name="partidos"
    )

    jornada = models.PositiveSmallIntegerField(default=1)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(
        max_length=15, choices=ESTADOS_PARTIDO, default="programado"
    )

    # El resultado solo se carga cuando el partido pasa a "jugado".
    goles_local = models.PositiveSmallIntegerField(null=True, blank=True)
    goles_visitante = models.PositiveSmallIntegerField(null=True, blank=True)

    codigo = models.CharField(max_length=20, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    # Quien programo el partido sale del token, no del body.
    programado_por = models.ForeignKey(
        "usuarios.UsuarioModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partidos_programados",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "partidos"
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ["-fecha", "-hora"]

    def __str__(self):
        return (
            f"{self.equipo_local.nombre} vs {self.equipo_visitante.nombre} "
            f"({self.fecha})"
        )

    @property
    def marcador(self):
        if self.estado != "jugado" or self.goles_local is None:
            return None
        return f"{self.goles_local} - {self.goles_visitante}"


class ResenaModel(models.Model):
    """El comentario de un hincha sobre un partido ya jugado."""

    partido = models.ForeignKey(
        PartidoModel, on_delete=models.CASCADE, related_name="resenas"
    )
    autor = models.ForeignKey(
        "usuarios.UsuarioModel", on_delete=models.CASCADE, related_name="resenas"
    )
    comentario = models.TextField()
    puntuacion = models.PositiveSmallIntegerField(default=5)
    estado = models.CharField(
        max_length=15, choices=ESTADOS_RESENA, default="pendiente"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resenas"
        verbose_name = "Resena"
        verbose_name_plural = "Resenas"
        ordering = ["-created_at"]
        # Un hincha opina una sola vez por partido.
        constraints = [
            models.UniqueConstraint(
                fields=["partido", "autor"], name="una_resena_por_usuario_y_partido"
            )
        ]

    def __str__(self):
        return f"{self.autor.username} - {self.puntuacion}/5"
