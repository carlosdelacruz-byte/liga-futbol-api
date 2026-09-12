from rest_framework import generics

from usuarios.permissions import EsAdminOrReadOnly

from .models import EquipoModel, EstadioModel, LigaModel
from .serializers import EquipoSerializer, EstadioSerializer, LigaSerializer


class LigaListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = LigaModel.objects.all()
   serializer_class = LigaSerializer


class LigaDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = LigaModel.objects.all()
   serializer_class = LigaSerializer


class EquipoListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EquipoModel.objects.all()
   serializer_class = EquipoSerializer


class EquipoDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EquipoModel.objects.all()
   serializer_class = EquipoSerializer


class EstadioListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EstadioModel.objects.all()
   serializer_class = EstadioSerializer


class EstadioDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = EstadioModel.objects.all()
   serializer_class = EstadioSerializer
