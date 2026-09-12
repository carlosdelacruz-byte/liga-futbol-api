from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ligas.models import LigaModel
from usuarios.permissions import EsAdminOrReadOnly
from utils.helpers import EmailHelper

from .models import PartidoModel, ResenaModel
from .serializers import PartidoSerializer, ResenaSerializer
from .services import DisponibilidadService, TablaPosicionesService, asignar_codigo


class PartidoListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = PartidoModel.objects.all()
   serializer_class = PartidoSerializer

   def perform_create(self, serializer):
      partido = serializer.save(programado_por=self.request.user)
      asignar_codigo(partido)
      EmailHelper.enviar(
         asunto=f"Partido programado {partido.codigo}",
         cuerpo=f"Se programo {partido.equipo_local.nombre} vs "
                f"{partido.equipo_visitante.nombre}\n"
                f"Fecha: {partido.fecha} a las {partido.hora}\n"
                f"Estadio: {partido.estadio.nombre}",
         para_email=self.request.user.email
      )


class PartidoDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = PartidoModel.objects.all()
   serializer_class = PartidoSerializer

   def destroy(self, request, *args, **kwargs):
      partido = self.get_object()
      if partido.estado == "jugado":
         return Response(
            {"detail": "Un partido ya jugado no se puede cancelar."},
            status=400
         )
      partido.estado = "cancelado"
      partido.save()
      return Response(status=204)


@extend_schema(
   summary="Estadios libres en una fecha y hora",
   description="Devuelve los estadios sin partido en esa franja y los "
               "equipos que ya juegan ese dia.",
   responses={200: None}
)
class DisponibilidadView(APIView):
   permission_classes = [IsAuthenticated]

   def get(self, request):
      fecha = request.query_params.get("fecha")
      hora = request.query_params.get("hora")

      if not fecha or not hora:
         return Response(
            {"error": "fecha y hora son obligatorias (?fecha=AAAA-MM-DD&hora=HH:MM)"},
            status=400
         )

      try:
         fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
         hora_dt = datetime.strptime(hora, "%H:%M").time()
      except ValueError:
         return Response(
            {"error": "Formato invalido. Se espera fecha=AAAA-MM-DD y hora=HH:MM."},
            status=400
         )

      estadios = DisponibilidadService.estadios_libres(fecha_dt, hora_dt)
      equipos_ocupados = DisponibilidadService.equipos_ocupados(fecha_dt)

      return Response({
         "fecha": fecha,
         "hora": hora,
         "estadios_libres": [
            {
               "id": estadio.id,
               "nombre": estadio.nombre,
               "ciudad": estadio.ciudad,
               "capacidad": estadio.capacidad,
               "equipo": estadio.equipo.nombre
            }
            for estadio in estadios
         ],
         "equipos_con_partido_ese_dia": equipos_ocupados
      })


@extend_schema(
   summary="Tabla de posiciones de una liga",
   description="Calcula puntos, partidos jugados y goles a partir de los "
               "partidos en estado jugado.",
   responses={200: None}
)
class TablaPosicionesView(APIView):
   permission_classes = [IsAuthenticated]

   def get(self, request, liga_id):
      if not LigaModel.objects.filter(pk=liga_id).exists():
         return Response({"detail": "La liga no existe."}, status=404)

      tabla = TablaPosicionesService.calcular(liga_id)
      return Response(tabla)


class ResenaListCreateView(generics.ListCreateAPIView):
   permission_classes = [IsAuthenticated]
   serializer_class = ResenaSerializer

   def get_queryset(self):
      if self.request.user.rol == "admin":
         return ResenaModel.objects.all()
      return ResenaModel.objects.filter(estado="publicada") | \
             ResenaModel.objects.filter(autor=self.request.user)

   def perform_create(self, serializer):
      serializer.save(autor=self.request.user)


class ResenaDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [IsAuthenticated]
   serializer_class = ResenaSerializer

   def get_queryset(self):
      if self.request.user.rol == "admin":
         return ResenaModel.objects.all()
      return ResenaModel.objects.filter(autor=self.request.user)
