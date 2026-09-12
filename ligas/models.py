from django.db import models


class LigaModel(models.Model):
    """El torneo. La cabeza de la jerarquia: una liga agrupa a sus equipos."""

    nombre = models.CharField(max_length=100, null=False, blank=False)
    temporada = models.CharField(max_length=9, help_text="Formato 2025-2026")
    pais = models.CharField(max_length=60)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ligas"
        verbose_name = "Liga"
        verbose_name_plural = "Ligas"
        ordering = ["nombre"]
        # La misma liga puede repetirse por temporada, pero no dos veces
        # en la misma temporada.
        constraints = [
            models.UniqueConstraint(
                fields=["nombre", "temporada"], name="liga_unica_por_temporada"
            )
        ]

    def __str__(self):
        return f"{self.nombre} {self.temporada}"


class EquipoModel(models.Model):
    """Un club dentro de una liga."""

    nombre = models.CharField(max_length=100, null=False, blank=False)
    ciudad = models.CharField(max_length=80)
    fundacion = models.PositiveIntegerField(help_text="Anio de fundacion del club")
    escudo_url = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # PROTECT: no se borra una liga que todavia tiene equipos colgando.
    liga = models.ForeignKey(
        LigaModel, on_delete=models.PROTECT, related_name="equipos"
    )

    class Meta:
        db_table = "equipos"
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["liga", "nombre"], name="equipo_unico_por_liga"
            )
        ]

    def __str__(self):
        return self.nombre


class EstadioModel(models.Model):
    """La cancha donde juega un equipo. Es el recurso que se reserva."""

    nombre = models.CharField(max_length=120)
    ciudad = models.CharField(max_length=80)
    capacidad = models.PositiveIntegerField()
    direccion = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    equipo = models.ForeignKey(
        EquipoModel, on_delete=models.PROTECT, related_name="estadios"
    )

    class Meta:
        db_table = "estadios"
        verbose_name = "Estadio"
        verbose_name_plural = "Estadios"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["equipo", "nombre"], name="estadio_unico_por_equipo"
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.equipo.nombre})"
