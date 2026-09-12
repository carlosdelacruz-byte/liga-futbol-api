import datetime

from rest_framework import serializers

from .models import EquipoModel, EstadioModel, LigaModel

ANIO_ACTUAL = datetime.date.today().year


class LigaSerializer(serializers.ModelSerializer):
   class Meta:
      model = LigaModel
      fields = ["id", "nombre", "temporada", "pais", "activa", "created_at"]

   def validate_nombre(self, value):
      if len(value.strip()) < 3:
         raise serializers.ValidationError(
            "El nombre de la liga debe tener al menos 3 caracteres."
         )
      return value.strip()

   def validate_temporada(self, value):
      partes = value.strip().split("-")
      if len(partes) != 2:
         raise serializers.ValidationError(
            "La temporada debe tener el formato AAAA-AAAA (por ejemplo 2025-2026)."
         )
      if not partes[0].isdigit() or not partes[1].isdigit():
         raise serializers.ValidationError(
            "La temporada debe tener el formato AAAA-AAAA (por ejemplo 2025-2026)."
         )
      if len(partes[0]) != 4 or len(partes[1]) != 4:
         raise serializers.ValidationError(
            "La temporada debe tener el formato AAAA-AAAA (por ejemplo 2025-2026)."
         )

      inicio = int(partes[0])
      fin = int(partes[1])
      if fin != inicio + 1:
         raise serializers.ValidationError(
            "Los anios de la temporada deben ser consecutivos."
         )
      if inicio < 1900 or inicio > ANIO_ACTUAL + 5:
         raise serializers.ValidationError(
            f"El anio de inicio debe estar entre 1900 y {ANIO_ACTUAL + 5}."
         )
      return value.strip()


class EquipoSerializer(serializers.ModelSerializer):
   class Meta:
      model = EquipoModel
      fields = [
         "id", "nombre", "ciudad", "fundacion",
         "escudo_url", "activo", "liga", "created_at"
      ]

   def validate_nombre(self, value):
      if len(value.strip()) < 3:
         raise serializers.ValidationError(
            "El nombre del equipo debe tener al menos 3 caracteres."
         )
      return value.strip()

   def validate_fundacion(self, value):
      if value < 1857:
         raise serializers.ValidationError(
            "El anio de fundacion no puede ser anterior a 1857."
         )
      if value > ANIO_ACTUAL:
         raise serializers.ValidationError(
            "El anio de fundacion no puede estar en el futuro."
         )
      return value

   def validate_liga(self, value):
      if not value.activa:
         raise serializers.ValidationError(
            "No se pueden inscribir equipos en una liga inactiva."
         )
      return value

   def to_representation(self, instance):
      data = super().to_representation(instance)
      data["liga"] = LigaSerializer(instance.liga).data
      return data


class EstadioSerializer(serializers.ModelSerializer):
   class Meta:
      model = EstadioModel
      fields = [
         "id", "nombre", "ciudad", "capacidad",
         "direccion", "equipo", "created_at"
      ]

   def validate_capacidad(self, value):
      if value < 500:
         raise serializers.ValidationError(
            "Un estadio profesional necesita al menos 500 localidades."
         )
      if value > 200000:
         raise serializers.ValidationError(
            "La capacidad declarada supera la del estadio mas grande del mundo."
         )
      return value

   def validate_equipo(self, value):
      if not value.activo:
         raise serializers.ValidationError(
            "No se puede registrar un estadio para un equipo inactivo."
         )
      return value
