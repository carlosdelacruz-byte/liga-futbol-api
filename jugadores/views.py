from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.response import Response

from usuarios.permissions import EsAdminOrReadOnly, EsStaffDeLigaOrReadOnly

from .models import JugadorModel, PosicionModel
from .serializers import JugadorSerializer, PosicionSerializer


@extend_schema_view(
    get=extend_schema(tags=["jugadores"], summary="Listar posiciones"),
    post=extend_schema(tags=["jugadores"], summary="Crear posicion (solo admin)"),
)
class PosicionListCreateView(generics.ListCreateAPIView):
    queryset = PosicionModel.objects.all()
    serializer_class = PosicionSerializer
    permission_classes = [EsAdminOrReadOnly]
    search_fields = ["nombre", "abreviatura"]
    ordering_fields = ["nombre"]


@extend_schema_view(
    get=extend_schema(tags=["jugadores"]),
    put=extend_schema(tags=["jugadores"]),
    patch=extend_schema(tags=["jugadores"]),
    delete=extend_schema(tags=["jugadores"]),
)
class PosicionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PosicionModel.objects.all()
    serializer_class = PosicionSerializer
    permission_classes = [EsAdminOrReadOnly]


@extend_schema_view(
    get=extend_schema(tags=["jugadores"], summary="Listar jugadores"),
    post=extend_schema(tags=["jugadores"], summary="Fichar jugador (admin o DT)"),
)
class JugadorListCreateView(generics.ListCreateAPIView):
    """El listado muestra solo jugadores activos; el filtro permite ver todos."""

    serializer_class = JugadorSerializer
    permission_classes = [EsStaffDeLigaOrReadOnly]
    filterset_fields = ["equipo", "posicion", "nacionalidad", "pie_habil", "activo"]
    search_fields = ["nombres", "apellidos", "nacionalidad"]
    ordering_fields = ["dorsal", "apellidos", "fecha_nacimiento"]

    def get_queryset(self):
        consulta = JugadorModel.objects.select_related("equipo", "posicion")
        # Sin filtro explicito se listan solo los que estan en actividad.
        if "activo" not in self.request.query_params:
            consulta = consulta.filter(activo=True)
        return consulta


@extend_schema_view(
    get=extend_schema(tags=["jugadores"]),
    put=extend_schema(tags=["jugadores"]),
    patch=extend_schema(tags=["jugadores"]),
    delete=extend_schema(tags=["jugadores"], summary="Baja logica del jugador"),
)
class JugadorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = JugadorModel.objects.select_related("equipo", "posicion").all()
    serializer_class = JugadorSerializer
    permission_classes = [EsStaffDeLigaOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        """
        Baja logica: el jugador queda en el historial pero libera el cupo
        del plantel. Borrarlo de verdad romperia los partidos ya jugados.
        """
        jugador = self.get_object()
        jugador.activo = False
        jugador.save(update_fields=["activo"])
        return Response(status=status.HTTP_204_NO_CONTENT)
