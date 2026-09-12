from drf_spectacular.utils import extend_schema, extend_schema_view

from rest_framework import generics

from usuarios.permissions import EsAdminOrReadOnly

from .models import EquipoModel, EstadioModel, LigaModel
from .serializers import EquipoSerializer, EstadioSerializer, LigaSerializer


# ---------------------------------------------------------------------------
# Ligas
# ---------------------------------------------------------------------------


@extend_schema_view(
    get=extend_schema(tags=["ligas"], summary="Listar ligas"),
    post=extend_schema(tags=["ligas"], summary="Crear liga (solo admin)"),
)
class LigaListCreateView(generics.ListCreateAPIView):
    queryset = LigaModel.objects.prefetch_related("equipos").all()
    serializer_class = LigaSerializer
    permission_classes = [EsAdminOrReadOnly]
    filterset_fields = ["pais", "temporada", "activa"]
    search_fields = ["nombre", "pais"]
    ordering_fields = ["nombre", "temporada", "created_at"]


@extend_schema_view(
    get=extend_schema(tags=["ligas"]),
    put=extend_schema(tags=["ligas"]),
    patch=extend_schema(tags=["ligas"]),
    delete=extend_schema(tags=["ligas"]),
)
class LigaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LigaModel.objects.prefetch_related("equipos").all()
    serializer_class = LigaSerializer
    permission_classes = [EsAdminOrReadOnly]


# ---------------------------------------------------------------------------
# Equipos
# ---------------------------------------------------------------------------


@extend_schema_view(
    get=extend_schema(tags=["ligas"], summary="Listar equipos"),
    post=extend_schema(tags=["ligas"], summary="Crear equipo (solo admin)"),
)
class EquipoListCreateView(generics.ListCreateAPIView):
    queryset = EquipoModel.objects.select_related("liga").all()
    serializer_class = EquipoSerializer
    permission_classes = [EsAdminOrReadOnly]
    filterset_fields = ["liga", "ciudad", "activo"]
    search_fields = ["nombre", "ciudad"]
    ordering_fields = ["nombre", "fundacion"]


@extend_schema_view(
    get=extend_schema(tags=["ligas"]),
    put=extend_schema(tags=["ligas"]),
    patch=extend_schema(tags=["ligas"]),
    delete=extend_schema(tags=["ligas"]),
)
class EquipoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EquipoModel.objects.select_related("liga").all()
    serializer_class = EquipoSerializer
    permission_classes = [EsAdminOrReadOnly]


# ---------------------------------------------------------------------------
# Estadios
# ---------------------------------------------------------------------------


@extend_schema_view(
    get=extend_schema(tags=["ligas"], summary="Listar estadios"),
    post=extend_schema(tags=["ligas"], summary="Crear estadio (solo admin)"),
)
class EstadioListCreateView(generics.ListCreateAPIView):
    queryset = EstadioModel.objects.select_related("equipo").all()
    serializer_class = EstadioSerializer
    permission_classes = [EsAdminOrReadOnly]
    filterset_fields = ["equipo", "ciudad"]
    search_fields = ["nombre", "ciudad"]
    ordering_fields = ["nombre", "capacidad"]


@extend_schema_view(
    get=extend_schema(tags=["ligas"]),
    put=extend_schema(tags=["ligas"]),
    patch=extend_schema(tags=["ligas"]),
    delete=extend_schema(tags=["ligas"]),
)
class EstadioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EstadioModel.objects.select_related("equipo").all()
    serializer_class = EstadioSerializer
    permission_classes = [EsAdminOrReadOnly]
