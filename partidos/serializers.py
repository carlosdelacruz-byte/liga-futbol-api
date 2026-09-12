import datetime

from rest_framework import serializers

from .models import PartidoModel, ResenaModel
from .services import DisponibilidadService

# De que estado se puede pasar a cual.
# Lo que no esta en la lista, no se permite.
# Un partido jugado o cancelado ya no se mueve: es historia.
TRANSICIONES = {
   "programado": ["jugado", "suspendido", "cancelado"],
   "suspendido": ["programado", "cancelado"],
   "jugado": [],
   "cancelado": []
}

# Cuantos dias hacia adelante se puede programar como maximo
DIAS_MAXIMOS_A_FUTURO = 365


class PartidoSerializer(serializers.ModelSerializer):
   class Meta:
      model = PartidoModel
      fields = [
         "id", "codigo", "liga", "equipo_local", "equipo_visitante",
         "estadio", "jornada", "fecha", "hora", "estado",
         "goles_local", "goles_visitante", "observaciones",
         "programado_por", "created_at"
      ]
      # El codigo lo genera el backend y el responsable sale del token.
      # Si fueran escribibles, cualquiera inventaria codigos o programaria
      # partidos a nombre de otro.
      read_only_fields = ["codigo", "programado_por"]

   # VALIDACIONES DE UN SOLO CAMPO

   def validate_fecha(self, value):
      hoy = datetime.date.today()
      # Al programar un partido nuevo la fecha tiene que estar por delante
      if self.instance is None and value < hoy:
         raise serializers.ValidationError(
            "No se puede programar un partido en una fecha pasada."
         )
      if value > hoy + datetime.timedelta(days=DIAS_MAXIMOS_A_FUTURO):
         raise serializers.ValidationError(
            f"No se puede programar con mas de {DIAS_MAXIMOS_A_FUTURO} "
            f"dias de anticipacion."
         )
      return value

   def validate_jornada(self, value):
      if value < 1 or value > 60:
         raise serializers.ValidationError("La jornada debe estar entre 1 y 60.")
      return value

   def validate_estado(self, value):
      # La maquina de estados: de programado se avanza, nunca se retrocede
      if self.instance and value != self.instance.estado:
         permitidas = TRANSICIONES.get(self.instance.estado, [])
         if value not in permitidas:
            if len(permitidas) == 0:
               raise serializers.ValidationError(
                  f"Un partido '{self.instance.estado}' ya no cambia de estado."
               )
            raise serializers.ValidationError(
               f"Transicion no permitida: {self.instance.estado} -> {value}. "
               f"Las validas son: {', '.join(permitidas)}."
            )
      return value

   # VALIDACION CRUZADA (necesita mirar varios campos a la vez)

   def validate(self, attrs):
      def dato(nombre):
         # El valor nuevo si vino en el body, si no el que ya tiene el partido
         if nombre in attrs:
            return attrs[nombre]
         return getattr(self.instance, nombre, None)

      liga = dato("liga")
      local = dato("equipo_local")
      visitante = dato("equipo_visitante")
      estadio = dato("estadio")
      fecha = dato("fecha")
      hora = dato("hora")
      estado = dato("estado") or "programado"
      goles_local = dato("goles_local")
      goles_visitante = dato("goles_visitante")

      errores = {}

      # 1. Un equipo no juega contra si mismo
      if local and visitante and local == visitante:
         errores["equipo_visitante"] = "El equipo visitante debe ser distinto del local."

      # 2. Los dos equipos tienen que competir en la liga del partido
      if liga:
         if local and local.liga_id != liga.id:
            errores["equipo_local"] = f"{local.nombre} no participa en {liga.nombre}."
         if visitante and visitante.liga_id != liga.id:
            errores["equipo_visitante"] = f"{visitante.nombre} no participa en {liga.nombre}."

      # 3. El resultado solo existe si el partido se jugo
      hay_goles = goles_local is not None or goles_visitante is not None
      if estado == "jugado":
         if goles_local is None or goles_visitante is None:
            errores["goles_local"] = (
               "Para marcar el partido como jugado hay que cargar ambos marcadores."
            )
      elif hay_goles:
         errores["goles_local"] = f"Un partido '{estado}' no puede tener marcador cargado."

      # Las reglas de agenda solo aplican mientras el partido ocupe la cancha
      if estado not in ["programado", "jugado"]:
         if errores:
            raise serializers.ValidationError(errores)
         return attrs

      # 4. El estadio tiene que estar libre en esa franja
      if estadio and fecha and hora:
         libres = DisponibilidadService.estadios_libres(
            fecha, hora, excluir_partido=self.instance
         )
         if not libres.filter(pk=estadio.pk).exists():
            errores["estadio"] = (
               f"{estadio.nombre} ya tiene un partido cerca de ese horario el {fecha}."
            )

      # 5. Ningun equipo juega dos partidos el mismo dia
      if fecha:
         ocupados = DisponibilidadService.equipos_ocupados(
            fecha, excluir_partido=self.instance
         )
         if local and local.id in ocupados and "equipo_local" not in errores:
            errores["equipo_local"] = f"{local.nombre} ya tiene un partido el {fecha}."
         if visitante and visitante.id in ocupados and "equipo_visitante" not in errores:
            errores["equipo_visitante"] = f"{visitante.nombre} ya tiene un partido el {fecha}."

      if errores:
         raise serializers.ValidationError(errores)
      return attrs

   def to_representation(self, instance):
      # En la respuesta devolvemos los nombres, no solo los ids
      data = super().to_representation(instance)
      data["liga_nombre"] = instance.liga.nombre
      data["equipo_local_nombre"] = instance.equipo_local.nombre
      data["equipo_visitante_nombre"] = instance.equipo_visitante.nombre
      data["estadio_nombre"] = instance.estadio.nombre
      if instance.estado == "jugado" and instance.goles_local is not None:
         data["marcador"] = f"{instance.goles_local} - {instance.goles_visitante}"
      else:
         data["marcador"] = None
      return data


class ResenaSerializer(serializers.ModelSerializer):
   class Meta:
      model = ResenaModel
      fields = [
         "id", "partido", "autor", "comentario",
         "puntuacion", "estado", "created_at"
      ]
      # El autor sale del token, nunca del body
      read_only_fields = ["autor"]

   def validate_puntuacion(self, value):
      if value < 1 or value > 5:
         raise serializers.ValidationError("La puntuacion va del 1 al 5.")
      return value

   def validate_comentario(self, value):
      if len(value.strip()) < 10:
         raise serializers.ValidationError(
            "El comentario debe tener al menos 10 caracteres."
         )
      return value.strip()

   def validate_partido(self, value):
      # Solo se opina de un partido que ya se jugo
      if value.estado != "jugado":
         raise serializers.ValidationError("Solo se pueden resenar partidos ya jugados.")
      return value

   def validate_estado(self, value):
      # Publicar u ocultar una resena es tarea del administrador
      request = self.context.get("request")
      if request and self.instance and value != self.instance.estado:
         if request.user.rol != "admin":
            raise serializers.ValidationError(
               "Solo el administrador puede moderar el estado de una resena."
            )
      return value

   def validate(self, attrs):
      # Un usuario deja una sola resena por partido
      request = self.context.get("request")
      partido = attrs.get("partido")

      if request and partido and self.instance is None:
         repetida = ResenaModel.objects.filter(
            partido=partido, autor=request.user
         ).exists()
         if repetida:
            raise serializers.ValidationError({
               "partido": "Ya dejaste una resena para este partido."
            })
      return attrs

   def to_representation(self, instance):
      data = super().to_representation(instance)
      data["autor_username"] = instance.autor.username
      data["partido_codigo"] = instance.partido.codigo
      return data
