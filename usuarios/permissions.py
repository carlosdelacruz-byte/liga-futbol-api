"""
Permisos por rol.

DRF sabe si estas autenticado, pero no conoce nuestro campo `rol`.
Ese afinado se escribe una vez aca y se reutiliza en todas las vistas.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def _es_admin(usuario):
    return bool(
        usuario
        and usuario.is_authenticated
        and (usuario.rol == "admin" or usuario.is_superuser)
    )


class EsAdmin(BasePermission):
    """Solo el administrador entra, lea o escriba."""

    message = "Esta accion es exclusiva del administrador."

    def has_permission(self, request, view):
        return _es_admin(request.user)


class EsAdminOrReadOnly(BasePermission):
    """
    Cualquier usuario logueado puede leer; escribir solo el admin.

    SAFE_METHODS son GET, HEAD y OPTIONS: las lecturas.
    """

    message = "Solo el administrador puede modificar este recurso."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return _es_admin(request.user)


class EsStaffDeLigaOrReadOnly(BasePermission):
    """
    Leer: cualquiera logueado. Escribir: admin o director tecnico.

    El DT arma el plantel (jugadores) pero no toca la estructura de la liga.
    """

    message = "Solo el administrador o un director tecnico pueden modificar esto."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and (usuario.rol in ("admin", "dt") or usuario.is_superuser)
        )


class EsAutorOrAdmin(BasePermission):
    """
    Permiso a nivel de objeto: cada quien edita lo suyo, el admin edita todo.

    Se usa en resenas y en el detalle de usuario.
    """

    message = "Solo podes modificar tus propios registros."

    def has_object_permission(self, request, view, obj):
        if _es_admin(request.user):
            return True
        if request.method in SAFE_METHODS:
            return True
        # El objeto puede llamar a su dueno `autor` (resena) o ser el usuario mismo.
        dueno = getattr(obj, "autor", obj)
        return dueno == request.user
