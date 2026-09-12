from django.urls import path

from .views import (
    JugadorDetailView,
    JugadorListCreateView,
    PosicionDetailView,
    PosicionListCreateView,
)

urlpatterns = [
    path("posiciones/", PosicionListCreateView.as_view(), name="posiciones-list"),
    path(
        "posiciones/<int:pk>/", PosicionDetailView.as_view(), name="posiciones-detail"
    ),
    path("jugadores/", JugadorListCreateView.as_view(), name="jugadores-list"),
    path("jugadores/<int:pk>/", JugadorDetailView.as_view(), name="jugadores-detail"),
]
