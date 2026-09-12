"""
Codigo transversal del proyecto.

Aca vive lo que no le pertenece a ningun dominio: las constantes compartidas
entre apps y el envio de correo. No es una app de Django, es un modulo comun.
"""

from django.conf import settings
from django.core.mail import EmailMessage

# Roles del sistema. Viven aca porque `usuarios` los define pero `partidos`
# y `ligas` tambien los consultan para decidir permisos.
ROLES = [
    ("admin", "Administrador"),
    ("dt", "Director tecnico"),
    ("hincha", "Hincha"),
]

# Cuanto dura un partido de punta a punta (90 minutos + entretiempo + margen
# para que el estadio se libere). Es la ventana que usamos para detectar que
# dos partidos chocan en el mismo estadio.
DURACION_PARTIDO_MINUTOS = 120


class EmailHelper:
    """Envio de correo en una sola linea, para no repetir el armado del mensaje."""

    @staticmethod
    def enviar(asunto, cuerpo, para_email):
        if not para_email:
            return False
        mensaje = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [para_email])
        # fail_silently: que un problema de correo nunca tumbe la peticion HTTP.
        mensaje.send(fail_silently=True)
        return True
