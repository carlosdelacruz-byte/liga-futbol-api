from rest_framework.permissions import BasePermission, SAFE_METHODS


class EsAdmin(BasePermission):
   message = "Esta accion es exclusiva del administrador."

   def has_permission(self, request, view):
      return bool(
         request.user
         and request.user.is_authenticated
         and request.user.rol == "admin"
      )


class EsAdminOrReadOnly(BasePermission):
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
   message = "Solo el administrador o un director tecnico pueden modificar esto."

   def has_permission(self, request, view):
      if request.method in SAFE_METHODS:
         return bool(request.user and request.user.is_authenticated)
      return bool(
         request.user
         and request.user.is_authenticated
         and request.user.rol in ["admin", "dt"]
      )
