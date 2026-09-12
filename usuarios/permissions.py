from rest_framework.permissions import BasePermission, SAFE_METHODS

# DRF no conoce nuestro campo `rol`: ese afinado lo escribimos nosotros
# una vez aca y lo reutilizamos en todas las vistas.
# SAFE_METHODS son GET, HEAD y OPTIONS: las lecturas.


class EsAdmin(BasePermission):
   # Solo el administrador entra, lea o escriba
   message = "Esta accion es exclusiva del administrador."

   def has_permission(self, request, view):
      return bool(
         request.user
         and request.user.is_authenticated
         and request.user.rol == "admin"
      )


class EsAdminOrReadOnly(BasePermission):
   # Cualquier usuario logueado puede leer, escribir solo el admin
   message = "Solo el administrador puede modificar este recurso."

   def has_permission(self, request, view):
      if request.method in SAFE_METHODS:
         return bool(request.user and request.user.is_authenticated)
      return bool(
         request.user
         and request.user.is_authenticated
         and request.user.rol == "admin"
      )


class EsStaffDeLigaOrReadOnly(BasePermission):
   # Leer: cualquiera logueado. Escribir: admin o director tecnico.
   # El DT arma el plantel pero no toca la estructura de la liga.
   message = "Solo el administrador o un director tecnico pueden modificar esto."

   def has_permission(self, request, view):
      if request.method in SAFE_METHODS:
         return bool(request.user and request.user.is_authenticated)
      return bool(
         request.user
         and request.user.is_authenticated
         and request.user.rol in ["admin", "dt"]
      )
