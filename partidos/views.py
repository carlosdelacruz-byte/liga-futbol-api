from datetime import datetime

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ligas.models import LigaModel
from usuarios.permissions import EsAdminOrReadOnly, EsAutorOrAdmin
from utils.helpers import EmailHelper

from .models import PartidoModel, ResenaModel
from .serializers import (
    PartidoSerializer,
    ResenaSerializer,
    TablaPosicionesSerializer,
)
from .services import DisponibilidadService, TablaPosicionesService, asignar_codigo


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@extend_schema_view(
    get=extend_schema(tags=["partidos"], summary="Listar el fixture"),
    post=extend_schema(tags=["partidos"], summary="Programar partido (solo admin)"),
)
class PartidoListCreateView(generics.ListCreateAPIView):
    queryset = PartidoModel.objects.select_related(
        "liga", "equipo_local", "equipo_visitante", "estadio"
    ).all()
    serializer_class = PartidoSerializer
    permission_classes = [EsAdminOrReadOnly]
    filterset_fields = ["liga", "estado", "jornada", "fecha", "estadio"]
    search_fields = ["codigo", "equipo_local__nombre", "equipo_visitante__nombre"]
    ordering_fields = ["fecha", "jornada", "created_at"]

    def perform_create(self, serializer):
        # El responsable sale del token, no del body.
        partido = serializer.save(programado_por=self.request.user)
        asignar_codigo(partido)

        EmailHelper.enviar(
            asunto=f"Partido programado {partido.codigo}",
            cuerpo=(
                f"Se programo {partido.equipo_local.nombre} vs "
                f"{partido.equipo_visitante.nombre}\n"
                f"Fecha: {partido.fecha} a las {partido.hora}\n"
                f"Estadio: {partido.estadio.nombre}"
            ),
            para_email=self.request.user.email,
        )


@extend_schema_view(
    get=extend_schema(tags=["partidos"]),
    put=extend_schema(tags=["partidos"]),
    patch=extend_schema(tags=["partidos"], summary="Actualizar estado o resultado"),
    delete=extend_schema(tags=["partidos"], summary="Cancelar partido (baja logica)"),
)
class PartidoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PartidoModel.objects.select_related(
        "liga", "equipo_local", "equipo_visitante", "estadio"
    ).all()
    serializer_class = PartidoSerializer
    permission_classes = [EsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        """
        Baja logica: el partido no se borra, se cancela.

        Queda en el historial pero deja de ocupar el estadio y la fecha,
        porque la disponibilidad solo mira programados y jugados.
        """
        partido = self.get_object()
        if partido.estado == "jugado":
            return Response(
                {"detail": "Un partido ya jugado no se puede cancelar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        partido.estado = "cancelado"
        partido.save(update_fields=["estado"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Disponibilidad de estadios
# ---------------------------------------------------------------------------


@extend_schema(
    tags=["partidos"],
    summary="Estadios libres en una fecha y hora",
    parameters=[
        OpenApiParameter("fecha", str, description="AAAA-MM-DD", required=True),
        OpenApiParameter("hora", str, description="HH:MM", required=True),
    ],
    responses={200: None},
)
class DisponibilidadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fecha = request.query_params.get("fecha")
        hora = request.query_params.get("hora")

        if not fecha or not hora:
            return Response(
                {
                    "error": "fecha y hora son obligatorias "
                    "(?fecha=AAAA-MM-DD&hora=HH:MM)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
            hora_dt = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            return Response(
                {"error": "Formato invalido. Se espera fecha=AAAA-MM-DD y hora=HH:MM."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estadios = DisponibilidadService.estadios_libres(fecha_dt, hora_dt)
        equipos_ocupados = DisponibilidadService.equipos_ocupados(fecha_dt)

        return Response(
            {
                "fecha": fecha,
                "hora": hora,
                "estadios_libres": [
                    {
                        "id": estadio.id,
                        "nombre": estadio.nombre,
                        "ciudad": estadio.ciudad,
                        "capacidad": estadio.capacidad,
                        "equipo": estadio.equipo.nombre,
                    }
                    for estadio in estadios
                ],
                "equipos_con_partido_ese_dia": sorted(equipos_ocupados),
            }
        )


# ---------------------------------------------------------------------------
# Tabla de posiciones
# ---------------------------------------------------------------------------


@extend_schema(
    tags=["partidos"],
    summary="Tabla de posiciones de una liga",
    responses={200: TablaPosicionesSerializer(many=True)},
)
class TablaPosicionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, liga_id):
        if not LigaModel.objects.filter(pk=liga_id).exists():
            return Response(
                {"detail": "La liga no existe."}, status=status.HTTP_404_NOT_FOUND
            )
        tabla = TablaPosicionesService.calcular(liga_id)
        return Response(tabla)


# ---------------------------------------------------------------------------
# Resenas
# ---------------------------------------------------------------------------


@extend_schema_view(
    get=extend_schema(tags=["partidos"], summary="Listar resenas"),
    post=extend_schema(tags=["partidos"], summary="Dejar una resena"),
)
class ResenaListCreateView(generics.ListCreateAPIView):
    serializer_class = ResenaSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["partido", "estado", "puntuacion"]
    ordering_fields = ["created_at", "puntuacion"]

    def get_queryset(self):
        consulta = ResenaModel.objects.select_related("partido", "autor")
        usuario = self.request.user

        # Al generar el schema de Swagger no hay usuario logueado.
        if getattr(self, "swagger_fake_view", False) or not usuario.is_authenticated:
            return consulta.none()

        if usuario.rol == "admin" or usuario.is_superuser:
            return consulta
        # El resto ve las publicadas y, ademas, siempre las propias.
        return consulta.filter(Q(estado="publicada") | Q(autor=usuario))

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)


@extend_schema_view(
    get=extend_schema(tags=["partidos"]),
    put=extend_schema(tags=["partidos"]),
    patch=extend_schema(tags=["partidos"]),
    delete=extend_schema(tags=["partidos"]),
)
class ResenaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ResenaModel.objects.select_related("partido", "autor").all()
    serializer_class = ResenaSerializer
    permission_classes = [IsAuthenticated, EsAutorOrAdmin]
