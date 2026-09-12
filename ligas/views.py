# Dentro del views definimos la logica, es decir el comportamiento
# de nuestros endpoints.
# Los generics son clases con comportamientos ya definidos:
# ListCreateAPIView => Listar y crear
# RetrieveUpdateDestroyAPIView => Obtener, actualizar y eliminar

from rest_framework import generics

from usuarios.permissions import EsAdminOrReadOnly

from .models import EquipoModel, EstadioModel, LigaModel
from .serializers import EquipoSerializer, EstadioSerializer, LigaSerializer


# LIGAS

class LigaListCreateView(generics.ListCreateAPIView):
   # Para proteger un endpoint usando JWT:
   permission_classes = [EsAdminOrReadOnly]
   queryset = LigaModel.objects.all()
   serializer_class = LigaSerializer


class LigaDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = LigaModel.objects.all()
   serializer_class = LigaSerializer


# EQUIPOS

class EquipoListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EquipoModel.objects.all()
   serializer_class = EquipoSerializer


class EquipoDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EquipoModel.objects.all()
   serializer_class = EquipoSerializer


# ESTADIOS

class EstadioListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EstadioModel.objects.all()
   serializer_class = EstadioSerializer


class EstadioDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EstadioModel.objects.all()
   serializer_class = EstadioSerializer
