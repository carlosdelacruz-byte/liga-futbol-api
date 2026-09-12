from django.conf import settings
from django.core.mail import EmailMessage

ROLES = [
   ("admin", "Administrador"),
   ("dt", "Director tecnico"),
   ("hincha", "Hincha")
]

DURACION_PARTIDO_MINUTOS = 120


class EmailHelper:
   @staticmethod
   def enviar(asunto, cuerpo, para_email):
      if not para_email:
         return False
      email = EmailMessage(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [para_email])
      email.send(fail_silently=True)
      return True
