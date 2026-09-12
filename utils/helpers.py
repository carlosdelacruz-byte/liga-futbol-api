# utils NO es una app: es el modulo transversal del proyecto.
# Aca vive el codigo que no le pertenece a ningun dominio:
# las constantes compartidas entre apps y el envio de correo.

from django.conf import settings
from django.core.mail import EmailMessage

# Los roles del sistema. Viven aca porque `usuarios` los define
# pero `ligas`, `jugadores` y `partidos` tambien los consultan.
ROLES = [
   ("admin", "Administrador"),
   ("dt", "Director tecnico"),
   ("hincha", "Hincha")
]

# Cuanto ocupa un partido de punta a punta: 90 minutos mas el
# entretiempo y un margen para que el estadio se libere.
# Es la ventana que usamos para detectar que dos partidos chocan.
DURACION_PARTIDO_MINUTOS = 120


class EmailHelper:

   @staticmethod
   def enviar(asunto, cuerpo, para_email):
      if not para_email:
         return False
      email = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [para_email])
      # fail_silently: que un problema de correo nunca tumbe la peticion HTTP
      email.send(fail_silently=True)
      return True
