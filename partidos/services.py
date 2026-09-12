# Los services guardan la logica de negocio que necesita consultar la base.
# Las vistas piden y responden, aca vive el como se calcula.

from datetime import datetime, timedelta

from django.db import transaction

from ligas.models import EquipoModel, EstadioModel
from utils.helpers import DURACION_PARTIDO_MINUTOS

from .models import PartidoModel

DURACION_PARTIDO = timedelta(minutes=DURACION_PARTIDO_MINUTOS)

# Solo estos estados ocupan la cancha.
# Los suspendidos y cancelados liberan la fecha.
ESTADOS_QUE_OCUPAN = ["programado", "jugado"]


class DisponibilidadService:

   @staticmethod
   def estadios_libres(fecha, hora, excluir_partido=None):
      # Responde: que estadios estan libres en tal fecha y hora
      inicio = datetime.combine(fecha, hora)
      fin = inicio + DURACION_PARTIDO

      partidos = PartidoModel.objects.filter(fecha=fecha, estado__in=ESTADOS_QUE_OCUPAN)
      if excluir_partido:
         partidos = partidos.exclude(pk=excluir_partido.pk)

      ocupados = []
      for partido in partidos:
         inicio_p = datetime.combine(partido.fecha, partido.hora)
         fin_p = inicio_p + DURACION_PARTIDO
         # Dos franjas se pisan si cada una empieza antes de que termine la otra
         if inicio_p < fin and inicio < fin_p:
            ocupados.append(partido.estadio_id)

      return EstadioModel.objects.exclude(id__in=ocupados)

   @staticmethod
   def equipos_ocupados(fecha, excluir_partido=None):
      # Que equipos ya tienen partido ese dia.
      # Aca no miramos la hora: un plantel no juega dos veces en la misma
      # jornada, aunque sea a diez horas de diferencia.
      partidos = PartidoModel.objects.filter(fecha=fecha, estado__in=ESTADOS_QUE_OCUPAN)
      if excluir_partido:
         partidos = partidos.exclude(pk=excluir_partido.pk)

      ocupados = []
      for partido in partidos:
         ocupados.append(partido.equipo_local_id)
         ocupados.append(partido.equipo_visitante_id)
      return ocupados


def asignar_codigo(partido):
   # Le pone el codigo publico al partido (PAR-0001).
   # select_for_update bloquea la fila mientras se escribe: si dos personas
   # programan partidos a la vez, ninguna pisa el codigo de la otra.
   with transaction.atomic():
      PartidoModel.objects.select_for_update().get(pk=partido.pk)
      partido.codigo = f"PAR-{partido.id:04d}"
      partido.save(update_fields=["codigo"])
   return partido


class TablaPosicionesService:
   PUNTOS_VICTORIA = 3
   PUNTOS_EMPATE = 1

   @staticmethod
   def calcular(liga_id):
      # Arma la tabla recorriendo los partidos ya jugados.
      # Cada partido se mira UNA sola vez y suma para sus dos equipos.

      tabla = {}
      for equipo in EquipoModel.objects.filter(liga_id=liga_id):
         tabla[equipo.id] = {
            "equipo_id": equipo.id,
            "equipo": equipo.nombre,
            "escudo_url": equipo.escudo_url,
            "puntos": 0,
            "jugados": 0,
            "ganados": 0,
            "empatados": 0,
            "perdidos": 0,
            "goles_favor": 0,
            "goles_contra": 0,
            "diferencia_goles": 0
         }

      partidos = PartidoModel.objects.filter(liga_id=liga_id, estado="jugado")

      for partido in partidos:
         local = tabla.get(partido.equipo_local_id)
         visitante = tabla.get(partido.equipo_visitante_id)
         if not local or not visitante:
            continue

         goles_local = partido.goles_local
         goles_visitante = partido.goles_visitante

         local["jugados"] = local["jugados"] + 1
         visitante["jugados"] = visitante["jugados"] + 1

         local["goles_favor"] = local["goles_favor"] + goles_local
         local["goles_contra"] = local["goles_contra"] + goles_visitante
         visitante["goles_favor"] = visitante["goles_favor"] + goles_visitante
         visitante["goles_contra"] = visitante["goles_contra"] + goles_local

         if goles_local > goles_visitante:
            local["ganados"] = local["ganados"] + 1
            local["puntos"] = local["puntos"] + TablaPosicionesService.PUNTOS_VICTORIA
            visitante["perdidos"] = visitante["perdidos"] + 1
         elif goles_local < goles_visitante:
            visitante["ganados"] = visitante["ganados"] + 1
            visitante["puntos"] = visitante["puntos"] + TablaPosicionesService.PUNTOS_VICTORIA
            local["perdidos"] = local["perdidos"] + 1
         else:
            local["empatados"] = local["empatados"] + 1
            visitante["empatados"] = visitante["empatados"] + 1
            local["puntos"] = local["puntos"] + TablaPosicionesService.PUNTOS_EMPATE
            visitante["puntos"] = visitante["puntos"] + TablaPosicionesService.PUNTOS_EMPATE

      filas = list(tabla.values())
      for fila in filas:
         fila["diferencia_goles"] = fila["goles_favor"] - fila["goles_contra"]

      # Criterios de desempate: puntos, diferencia de gol y goles a favor
      filas.sort(key=lambda fila: (
         -fila["puntos"],
         -fila["diferencia_goles"],
         -fila["goles_favor"],
         fila["equipo"]
      ))

      posicion = 1
      for fila in filas:
         fila["posicion"] = posicion
         posicion = posicion + 1

      return filas
