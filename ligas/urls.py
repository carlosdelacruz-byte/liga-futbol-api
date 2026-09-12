from django.urls import path

from .views import (
    EquipoDetailView,
    EquipoListCreateView,
    EstadioDetailView,
    EstadioListCreateView,
    LigaDetailView,
    LigaListCreateView,
)

urlpatterns = [
    path("ligas/", LigaListCreateView.as_view(), name="ligas-list"),
    path("ligas/<int:pk>/", LigaDetailView.as_view(), name="ligas-detail"),
    path("equipos/", EquipoListCreateView.as_view(), name="equipos-list"),
    path("equipos/<int:pk>/", EquipoDetailView.as_view(), name="equipos-detail"),
    path("estadios/", EstadioListCreateView.as_view(), name="estadios-list"),
    path("estadios/<int:pk>/", EstadioDetailView.as_view(), name="estadios-detail"),
]
