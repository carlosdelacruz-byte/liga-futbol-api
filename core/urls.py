"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
   path('admin/', admin.site.urls),
   # API
   path('api/v1/', include('usuarios.urls')),
   path('api/v1/', include('ligas.urls')),
   path('api/v1/', include('jugadores.urls')),
   path('api/v1/', include('partidos.urls')),
   # Documentacion con Swagger
   path('schema/', SpectacularAPIView.as_view(), name='schema'),
   path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
