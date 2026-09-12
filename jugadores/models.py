from django.db import models


class PosicionModel(models.Model):
    """Arquero, defensa, mediocampista, delantero..."""

    nombre = models.CharField(max_length=50, unique=True)
    abreviatura = models.CharField(max_length=3, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "posiciones"
        verbose_name = "Posicion"
        verbose_name_plural = "Posiciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class JugadorModel(models.Model):
    """Un futbolista del plantel de un equipo."""

    PIE_HABIL = [
        ("derecho", "Derecho"),
        ("izquierdo", "Izquierdo"),
        ("ambidiestro", "Ambidiestro"),
    ]

    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    dorsal = models.PositiveSmallIntegerField()
    fecha_nacimiento = models.DateField()
    nacionalidad = models.CharField(max_length=60)
    altura_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    pie_habil = models.CharField(max_length=12, choices=PIE_HABIL, default="derecho")
    foto_url = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relacion que cruza de app: se escribe "app.Modelo" entre comillas
    # y Django la resuelve sola.
    equipo = models.ForeignKey(
        "ligas.EquipoModel", on_delete=models.PROTECT, related_name="jugadores"
    )
    posicion = models.ForeignKey(
        PosicionModel, on_delete=models.PROTECT, related_name="jugadores"
    )

    class Meta:
        db_table = "jugadores"
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"
        ordering = ["equipo", "dorsal"]
        # Dentro de un equipo el dorsal no se repite.
        constraints = [
            models.UniqueConstraint(
                fields=["equipo", "dorsal"], name="dorsal_unico_por_equipo"
            )
        ]

    def __str__(self):
        return f"{self.dorsal} - {self.nombres} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
