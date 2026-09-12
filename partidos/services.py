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

    El conteo se agrupa en la base de datos, en dos pasadas sobre la tabla
    de partidos: una mirando a los equipos como local y otra como visitante.

    Se hacen DOS consultas a proposito. Anotar las dos relaciones sobre
    EquipoModel en una sola consulta obliga a Django a unir la tabla de
    partidos dos veces, y esa union multiplica las filas: un equipo con 2
    partidos de local y 3 de visitante produce 6 filas, y los Sum terminan
    contando goles de mas. Agrupando sobre PartidoModel cada partido aporta
    exactamente una fila.
    """

    PUNTOS_VICTORIA = 3
    PUNTOS_EMPATE = 1

    @staticmethod
    def _estadisticas_por_lado(liga_id, es_local):
        """
        Agrupa los partidos jugados por equipo, desde un solo lado del campo.

        `es_local` decide que columna agrupa y cuales goles son a favor.
        """
        if es_local:
            campo_equipo = "equipo_local"
            goles_favor, goles_contra = "goles_local", "goles_visitante"
        else:
            campo_equipo = "equipo_visitante"
            goles_favor, goles_contra = "goles_visitante", "goles_local"

        filas = (
            PartidoModel.objects.filter(liga_id=liga_id, estado="jugado")
            .values(campo_equipo)
            .annotate(
                jugados=Count("id"),
                ganados=Count("id", filter=Q(**{f"{goles_favor}__gt": F(goles_contra)})),
                empatados=Count("id", filter=Q(**{goles_favor: F(goles_contra)})),
                goles_favor=Sum(goles_favor),
                goles_contra=Sum(goles_contra),
            )
        )
        return {fila[campo_equipo]: fila for fila in filas}

    @staticmethod
    def calcular(liga_id):
        como_local = TablaPosicionesService._estadisticas_por_lado(liga_id, True)
        como_visitante = TablaPosicionesService._estadisticas_por_lado(liga_id, False)

        vacio = {
            "jugados": 0,
            "ganados": 0,
            "empatados": 0,
            "goles_favor": 0,
            "goles_contra": 0,
        }

        tabla = []
        equipos = EquipoModel.objects.filter(liga_id=liga_id).values(
            "id", "nombre", "escudo_url"
        )

        for equipo in equipos:
            local = como_local.get(equipo["id"], vacio)
            visita = como_visitante.get(equipo["id"], vacio)

            def total(clave):
                return (local[clave] or 0) + (visita[clave] or 0)

            jugados = total("jugados")
            ganados = total("ganados")
            empatados = total("empatados")
            goles_favor = total("goles_favor")
            goles_contra = total("goles_contra")

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
                    "perdidos": jugados - ganados - empatados,
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
