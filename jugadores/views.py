from rest_framework import generics
from rest_framework.response import Response

from usuarios.permissions import EsAdminOrReadOnly, EsStaffDeLigaOrReadOnly

from .models import JugadorModel, PosicionModel
from .serializers import JugadorSerializer, PosicionSerializer


class PosicionListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = PosicionModel.objects.all()
   serializer_class = PosicionSerializer


class PosicionDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsAdminOrReadOnly]
   queryset = PosicionModel.objects.all()
   serializer_class = PosicionSerializer


class JugadorListCreateView(generics.ListCreateAPIView):
   permission_classes = [EsStaffDeLigaOrReadOnly]
   queryset = JugadorModel.objects.filter(activo=True)
   serializer_class = JugadorSerializer


class JugadorDetailView(generics.RetrieveUpdateDestroyAPIView):
   permission_classes = [EsStaffDeLigaOrReadOnly]
   queryset = JugadorModel.objects.all()
   serializer_class = JugadorSerializer

   def destroy(self, request, *args, **kwargs):
      jugador = self.get_object()
      jugador.activo = False
      jugador.save()
      return Response(status=204)
