from django.urls import path

from .views import (
    DisponibilidadView,
    PartidoDetailView,
    PartidoListCreateView,
    ResenaDetailView,
    ResenaListCreateView,
    TablaPosicionesView,
)

urlpatterns = [
    path(
        "partidos/disponibilidad/",
        DisponibilidadView.as_view(),
        name="partidos-disponibilidad",
    ),
    path(
        "partidos/tabla/<int:liga_id>/",
        TablaPosicionesView.as_view(),
        name="partidos-tabla",
    ),
    path("partidos/", PartidoListCreateView.as_view(), name="partidos-list"),
    path("partidos/<int:pk>/", PartidoDetailView.as_view(), name="partidos-detail"),
    path("resenas/", ResenaListCreateView.as_view(), name="resenas-list"),
    path("resenas/<int:pk>/", ResenaDetailView.as_view(), name="resenas-detail"),
]
