"""
Logica de negocio de los partidos.

Las vistas piden y responden; las reglas que necesitan consultar la base
(disponibilidad, codigo, tabla de posiciones) viven aca.
"""

from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Count, F, Q, Sum

from ligas.models import EquipoModel, EstadioModel
from utils.helpers import DURACION_PARTIDO_MINUTOS

from .models import PartidoModel

DURACION_PARTIDO = timedelta(minutes=DURACION_PARTIDO_MINUTOS)

# Solo un partido programado ocupa el estadio. Los suspendidos y cancelados
# liberan la fecha.
ESTADOS_QUE_OCUPAN = ["programado", "jugado"]


def _ventana(fecha, hora):
    """Devuelve el inicio y el fin de la franja que ocupa un partido."""
    inicio = datetime.combine(fecha, hora)
    return inicio, inicio + DURACION_PARTIDO


def _se_cruzan(inicio_a, fin_a, inicio_b, fin_b):
    """Dos franjas se pisan si cada una empieza antes de que termine la otra."""
    return inicio_a < fin_b and inicio_b < fin_a


class DisponibilidadService:
    """Responde la pregunta: que estadios estan libres en tal fecha y hora."""

    @staticmethod
    def partidos_que_ocupan(fecha, excluir_partido=None):
        consulta = PartidoModel.objects.filter(
            fecha=fecha, estado__in=ESTADOS_QUE_OCUPAN
        )
        if excluir_partido is not None:
            consulta = consulta.exclude(pk=excluir_partido.pk)
        return consulta.select_related("estadio", "equipo_local", "equipo_visitante")

    @staticmethod
    def estadios_ocupados(fecha, hora, excluir_partido=None):
        """IDs de los estadios con un partido que se cruza con esa franja."""
        inicio, fin = _ventana(fecha, hora)
        ocupados = []
        for partido in DisponibilidadService.partidos_que_ocupan(
            fecha, excluir_partido
        ):
            inicio_p, fin_p = _ventana(partido.fecha, partido.hora)
            if _se_cruzan(inicio, fin, inicio_p, fin_p):
                ocupados.append(partido.estadio_id)
        return ocupados

    @staticmethod
    def estadios_libres(fecha, hora, excluir_partido=None):
        ocupados = DisponibilidadService.estadios_ocupados(
            fecha, hora, excluir_partido
        )
        return EstadioModel.objects.select_related("equipo").exclude(id__in=ocupados)

    @staticmethod
    def equipos_ocupados(fecha, excluir_partido=None):
        """
        IDs de equipos que ya tienen partido ese dia.

        Aca no miramos la hora: un plantel no juega dos veces en la misma
        jornada, aunque sea a diez horas de diferencia.
        """
        ocupados = set()
        for partido in DisponibilidadService.partidos_que_ocupan(
            fecha, excluir_partido
        ):
            ocupados.add(partido.equipo_local_id)
            ocupados.add(partido.equipo_visitante_id)
        return ocupados


@transaction.atomic
def asignar_codigo(partido):
    """
    Le pone el codigo publico al partido (PAR-0001).

    `select_for_update` bloquea la fila mientras se escribe: si dos personas
    programan partidos a la vez, ninguna pisa el codigo de la otra.
    """
    PartidoModel.objects.select_for_update().get(pk=partido.pk)
    partido.codigo = f"PAR-{partido.id:04d}"
    partido.save(update_fields=["codigo"])
    return partido


class TablaPosicionesService:
    """
    Arma la tabla de posiciones de una liga con los partidos ya jugados.

    Todo el conteo se resuelve en la base con agregaciones del ORM, no
    trayendo los partidos a Python.
    """

    PUNTOS_VICTORIA = 3
    PUNTOS_EMPATE = 1

    @staticmethod
    def calcular(liga_id):
        def contar(condicion):
            return Count("id", filter=condicion, distinct=True)

        equipos = (
            EquipoModel.objects.filter(liga_id=liga_id)
            .annotate(
                # --- Como local ---
                pj_local=contar(Q(partidos_de_local__estado="jugado")),
                ganados_local=contar(
                    Q(partidos_de_local__estado="jugado")
                    & Q(
                        partidos_de_local__goles_local__gt=F(
                            "partidos_de_local__goles_visitante"
                        )
                    )
                ),
                empatados_local=contar(
                    Q(partidos_de_local__estado="jugado")
                    & Q(
                        partidos_de_local__goles_local=F(
                            "partidos_de_local__goles_visitante"
                        )
                    )
                ),
                gf_local=Sum(
                    "partidos_de_local__goles_local",
                    filter=Q(partidos_de_local__estado="jugado"),
                ),
                gc_local=Sum(
                    "partidos_de_local__goles_visitante",
                    filter=Q(partidos_de_local__estado="jugado"),
                ),
                # --- Como visitante ---
                pj_visita=contar(Q(partidos_de_visitante__estado="jugado")),
                ganados_visita=contar(
                    Q(partidos_de_visitante__estado="jugado")
                    & Q(
                        partidos_de_visitante__goles_visitante__gt=F(
                            "partidos_de_visitante__goles_local"
                        )
                    )
                ),
                empatados_visita=contar(
                    Q(partidos_de_visitante__estado="jugado")
                    & Q(
                        partidos_de_visitante__goles_visitante=F(
                            "partidos_de_visitante__goles_local"
                        )
                    )
                ),
                gf_visita=Sum(
                    "partidos_de_visitante__goles_visitante",
                    filter=Q(partidos_de_visitante__estado="jugado"),
                ),
                gc_visita=Sum(
                    "partidos_de_visitante__goles_local",
                    filter=Q(partidos_de_visitante__estado="jugado"),
                ),
            )
            .values(
                "id",
                "nombre",
                "escudo_url",
                "pj_local",
                "ganados_local",
                "empatados_local",
                "gf_local",
                "gc_local",
                "pj_visita",
                "ganados_visita",
                "empatados_visita",
                "gf_visita",
                "gc_visita",
            )
        )

        tabla = []
        for equipo in equipos:
            cero = lambda valor: valor or 0  # noqa: E731

            jugados = cero(equipo["pj_local"]) + cero(equipo["pj_visita"])
            ganados = cero(equipo["ganados_local"]) + cero(equipo["ganados_visita"])
            empatados = cero(equipo["empatados_local"]) + cero(
                equipo["empatados_visita"]
            )
            perdidos = jugados - ganados - empatados
            goles_favor = cero(equipo["gf_local"]) + cero(equipo["gf_visita"])
            goles_contra = cero(equipo["gc_local"]) + cero(equipo["gc_visita"])

            tabla.append(
                {
                    "equipo_id": equipo["id"],
                    "equipo": equipo["nombre"],
                    "escudo_url": equipo["escudo_url"],
                    "puntos": (
                        ganados * TablaPosicionesService.PUNTOS_VICTORIA
                        + empatados * TablaPosicionesService.PUNTOS_EMPATE
                    ),
                    "jugados": jugados,
                    "ganados": ganados,
                    "empatados": empatados,
                    "perdidos": perdidos,
                    "goles_favor": goles_favor,
                    "goles_contra": goles_contra,
                    "diferencia_goles": goles_favor - goles_contra,
                }
            )

        # Criterios de desempate: puntos, diferencia de gol, goles a favor.
        tabla.sort(
            key=lambda fila: (
                -fila["puntos"],
                -fila["diferencia_goles"],
                -fila["goles_favor"],
                fila["equipo"],
            )
        )
        for posicion, fila in enumerate(tabla, start=1):
            fila["posicion"] = posicion
        return tabla
