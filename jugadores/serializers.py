import datetime

from rest_framework import serializers

from .models import JugadorModel, PosicionModel

EDAD_MINIMA = 15
EDAD_MAXIMA = 50
# Un plantel profesional no lleva mas de 30 fichas activas.
MAXIMO_JUGADORES_POR_EQUIPO = 30


class PosicionSerializer(serializers.ModelSerializer):
    total_jugadores = serializers.IntegerField(source="jugadores.count", read_only=True)

    class Meta:
        model = PosicionModel
        fields = ["id", "nombre", "abreviatura", "descripcion", "total_jugadores"]

    def validate_nombre(self, value):
        nombre = value.strip().title()
        consulta = PosicionModel.objects.filter(nombre__iexact=nombre)
        if self.instance:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise serializers.ValidationError("Esa posicion ya esta registrada.")
        return nombre

    def validate_abreviatura(self, value):
        abreviatura = value.strip().upper()
        if not abreviatura.isalpha():
            raise serializers.ValidationError(
                "La abreviatura solo admite letras (por ejemplo ARQ, DEF, MED, DEL)."
            )
        consulta = PosicionModel.objects.filter(abreviatura__iexact=abreviatura)
        if self.instance:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise serializers.ValidationError("Esa abreviatura ya esta en uso.")
        return abreviatura


class JugadorSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source="equipo.nombre", read_only=True)
    posicion_nombre = serializers.CharField(source="posicion.nombre", read_only=True)
    nombre_completo = serializers.CharField(read_only=True)
    edad = serializers.SerializerMethodField()

    class Meta:
        model = JugadorModel
        fields = [
            "id",
            "nombres",
            "apellidos",
            "nombre_completo",
            "dorsal",
            "fecha_nacimiento",
            "edad",
            "nacionalidad",
            "altura_cm",
            "pie_habil",
            "foto_url",
            "activo",
            "equipo",
            "equipo_nombre",
            "posicion",
            "posicion_nombre",
        ]
        # Apagamos el validador automatico de (equipo, dorsal): devuelve un
        # mensaje generico en non_field_errors. Nuestro validate() apunta al
        # campo dorsal y ademas dice quien lo esta usando.
        validators = []

    def get_edad(self, obj) -> int:
        hoy = datetime.date.today()
        nacimiento = obj.fecha_nacimiento
        return (
            hoy.year
            - nacimiento.year
            - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
        )

    def validate_dorsal(self, value):
        """En el futbol los dorsales van del 1 al 99."""
        if value < 1 or value > 99:
            raise serializers.ValidationError("El dorsal debe estar entre 1 y 99.")
        return value

    def validate_fecha_nacimiento(self, value):
        hoy = datetime.date.today()
        if value > hoy:
            raise serializers.ValidationError(
                "La fecha de nacimiento no puede estar en el futuro."
            )
        edad = hoy.year - value.year - ((hoy.month, hoy.day) < (value.month, value.day))
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
        if value is not None and not (140 <= value <= 220):
            raise serializers.ValidationError(
                "La altura debe estar entre 140 cm y 220 cm."
            )
        return value

    def validate(self, attrs):
        """
        Dos reglas que solo se pueden mirar con varios campos a la vez:
        el dorsal no se repite en el equipo y el plantel tiene un tope.
        """
        equipo = attrs.get("equipo", getattr(self.instance, "equipo", None))
        dorsal = attrs.get("dorsal", getattr(self.instance, "dorsal", None))

        if equipo and dorsal:
            ocupado = JugadorModel.objects.filter(equipo=equipo, dorsal=dorsal)
            if self.instance:
                ocupado = ocupado.exclude(pk=self.instance.pk)
            if ocupado.exists():
                raise serializers.ValidationError(
                    {
                        "dorsal": (
                            f"El dorsal {dorsal} ya lo usa "
                            f"{ocupado.first().nombre_completo} en {equipo.nombre}."
                        )
                    }
                )

        # El tope solo se controla al dar de alta o al mover a otro equipo.
        cambia_de_equipo = self.instance and self.instance.equipo_id != getattr(
            equipo, "id", None
        )
        if equipo and (self.instance is None or cambia_de_equipo):
            plantel = JugadorModel.objects.filter(equipo=equipo, activo=True).count()
            if plantel >= MAXIMO_JUGADORES_POR_EQUIPO:
                raise serializers.ValidationError(
                    {
                        "equipo": (
                            f"{equipo.nombre} ya tiene {MAXIMO_JUGADORES_POR_EQUIPO} "
                            "jugadores activos, el plantel esta completo."
                        )
                    }
                )
        return attrs
