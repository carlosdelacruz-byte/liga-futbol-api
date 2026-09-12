import datetime

from rest_framework import serializers

from .models import JugadorModel, PosicionModel

EDAD_MINIMA = 15
EDAD_MAXIMA = 50
MAXIMO_JUGADORES_POR_EQUIPO = 30


class PosicionSerializer(serializers.ModelSerializer):
   class Meta:
      model = PosicionModel
      fields = ["id", "nombre", "abreviatura", "descripcion"]

   def validate_abreviatura(self, value):
      if not value.isalpha():
         raise serializers.ValidationError(
            "La abreviatura solo admite letras (por ejemplo ARQ, DEF, MED, DEL)."
         )
      return value.upper()


class JugadorSerializer(serializers.ModelSerializer):
   class Meta:
      model = JugadorModel
      fields = [
         "id", "nombres", "apellidos", "dorsal", "fecha_nacimiento",
         "nacionalidad", "altura_cm", "pie_habil", "foto_url",
         "activo", "equipo", "posicion"
      ]

   def validate_dorsal(self, value):
      if value < 1 or value > 99:
         raise serializers.ValidationError("El dorsal debe estar entre 1 y 99.")
      return value

   def validate_fecha_nacimiento(self, value):
      hoy = datetime.date.today()
      if value > hoy:
         raise serializers.ValidationError(
            "La fecha de nacimiento no puede estar en el futuro."
         )

      edad = hoy.year - value.year
      if (hoy.month, hoy.day) < (value.month, value.day):
         edad = edad - 1

      if edad < EDAD_MINIMA:
         raise serializers.ValidationError(
            f"El jugador debe tener al menos {EDAD_MINIMA} anios."
         )
      if edad > EDAD_MAXIMA:
         raise serializers.ValidationError(
            f"El jugador no puede superar los {EDAD_MAXIMA} anios."
         )
      return value

   def validate_altura_cm(self, value):
      if value is not None and (value < 140 or value > 220):
         raise serializers.ValidationError(
            "La altura debe estar entre 140 cm y 220 cm."
         )
      return value

   def validate(self, attrs):
      equipo = attrs.get("equipo")
      if self.instance and not equipo:
         equipo = self.instance.equipo

      if equipo:
         es_nuevo = self.instance is None
         cambia_de_equipo = self.instance and self.instance.equipo_id != equipo.id

         if es_nuevo or cambia_de_equipo:
            plantel = JugadorModel.objects.filter(equipo=equipo, activo=True).count()
            if plantel >= MAXIMO_JUGADORES_POR_EQUIPO:
               raise serializers.ValidationError({
                  "equipo": f"{equipo.nombre} ya tiene "
                            f"{MAXIMO_JUGADORES_POR_EQUIPO} jugadores activos, "
                            f"el plantel esta completo."
               })
      return attrs

   def to_representation(self, instance):
      data = super().to_representation(instance)
      data["equipo_nombre"] = instance.equipo.nombre
      data["posicion_nombre"] = instance.posicion.nombre
      return data
