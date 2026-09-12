import datetime

from rest_framework import serializers

from .models import EquipoModel, EstadioModel, LigaModel

ANIO_ACTUAL = datetime.date.today().year


class LigaSerializer(serializers.ModelSerializer):
    total_equipos = serializers.IntegerField(source="equipos.count", read_only=True)

    class Meta:
        model = LigaModel
        fields = [
            "id",
            "nombre",
            "temporada",
            "pais",
            "activa",
            "total_equipos",
            "created_at",
        ]
        # Apagamos el validador automatico del UniqueConstraint: devuelve un
        # mensaje generico en non_field_errors. Lo reemplaza nuestro validate(),
        # que apunta al campo exacto y compara sin distinguir mayusculas.
        validators = []

    def validate_nombre(self, value):
        nombre = value.strip()
        if len(nombre) < 3:
            raise serializers.ValidationError(
                "El nombre de la liga debe tener al menos 3 caracteres."
            )
        return nombre

    def validate_temporada(self, value):
        """
        La temporada se escribe 2025-2026 y los anios tienen que ser consecutivos.
        """
        temporada = value.strip()
        partes = temporada.split("-")
        if len(partes) != 2 or not all(p.isdigit() and len(p) == 4 for p in partes):
            raise serializers.ValidationError(
                "La temporada debe tener el formato AAAA-AAAA (por ejemplo 2025-2026)."
            )
        inicio, fin = int(partes[0]), int(partes[1])
        if fin != inicio + 1:
            raise serializers.ValidationError(
                "Los anios de la temporada deben ser consecutivos."
            )
        if inicio < 1900 or inicio > ANIO_ACTUAL + 5:
            raise serializers.ValidationError(
                f"El anio de inicio debe estar entre 1900 y {ANIO_ACTUAL + 5}."
            )
        return temporada

    def validate(self, attrs):
        """No se repite la misma liga en la misma temporada."""
        nombre = attrs.get("nombre", getattr(self.instance, "nombre", None))
        temporada = attrs.get("temporada", getattr(self.instance, "temporada", None))

        consulta = LigaModel.objects.filter(
            nombre__iexact=nombre, temporada=temporada
        )
        if self.instance:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise serializers.ValidationError(
                {"nombre": f"La liga '{nombre}' ya esta registrada en {temporada}."}
            )
        return attrs


class EquipoSerializer(serializers.ModelSerializer):
    liga_nombre = serializers.CharField(source="liga.nombre", read_only=True)
    total_jugadores = serializers.SerializerMethodField()

    class Meta:
        model = EquipoModel
        fields = [
            "id",
            "nombre",
            "ciudad",
            "fundacion",
            "escudo_url",
            "activo",
            "liga",
            "liga_nombre",
            "total_jugadores",
            "created_at",
        ]
        # Ver la nota en LigaSerializer: la unicidad la valida validate().
        validators = []

    def get_total_jugadores(self, obj) -> int:
        return obj.jugadores.filter(activo=True).count()

    def validate_nombre(self, value):
        nombre = value.strip()
        if len(nombre) < 3:
            raise serializers.ValidationError(
                "El nombre del equipo debe tener al menos 3 caracteres."
            )
        return nombre

    def validate_fundacion(self, value):
        """El primer club de futbol del mundo es de 1857: antes de eso no hay equipos."""
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

    def validate(self, attrs):
        """Dentro de una misma liga el nombre del equipo no se repite."""
        nombre = attrs.get("nombre", getattr(self.instance, "nombre", None))
        liga = attrs.get("liga", getattr(self.instance, "liga", None))

        if nombre and liga:
            consulta = EquipoModel.objects.filter(liga=liga, nombre__iexact=nombre)
            if self.instance:
                consulta = consulta.exclude(pk=self.instance.pk)
            if consulta.exists():
                raise serializers.ValidationError(
                    {"nombre": f"'{nombre}' ya participa en {liga.nombre}."}
                )
        return attrs


class EstadioSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source="equipo.nombre", read_only=True)

    class Meta:
        model = EstadioModel
        fields = [
            "id",
            "nombre",
            "ciudad",
            "capacidad",
            "direccion",
            "equipo",
            "equipo_nombre",
            "created_at",
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
