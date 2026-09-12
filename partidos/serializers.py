import datetime

from rest_framework import serializers

from .models import PartidoModel, ResenaModel
from .services import DisponibilidadService

# De que estado se puede pasar a cual. Lo que no esta en la lista, no se permite.
# Un partido jugado o cancelado ya no se mueve: es historia.
TRANSICIONES = {
    "programado": ["jugado", "suspendido", "cancelado"],
    "suspendido": ["programado", "cancelado"],
    "jugado": [],
    "cancelado": [],
}

# Cuantos dias hacia adelante se puede programar como maximo.
DIAS_MAXIMOS_A_FUTURO = 365


class PartidoSerializer(serializers.ModelSerializer):
    equipo_local_nombre = serializers.CharField(
        source="equipo_local.nombre", read_only=True
    )
    equipo_visitante_nombre = serializers.CharField(
        source="equipo_visitante.nombre", read_only=True
    )
    estadio_nombre = serializers.CharField(source="estadio.nombre", read_only=True)
    liga_nombre = serializers.CharField(source="liga.nombre", read_only=True)
    marcador = serializers.CharField(read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = PartidoModel
        fields = [
            "id",
            "codigo",
            "liga",
            "liga_nombre",
            "equipo_local",
            "equipo_local_nombre",
            "equipo_visitante",
            "equipo_visitante_nombre",
            "estadio",
            "estadio_nombre",
            "jornada",
            "fecha",
            "hora",
            "estado",
            "estado_display",
            "goles_local",
            "goles_visitante",
            "marcador",
            "observaciones",
            "programado_por",
            "created_at",
        ]
        # El codigo lo genera el backend y el responsable sale del token:
        # si fueran escribibles, cualquiera inventaria codigos o programaria
        # partidos a nombre de otro.
        read_only_fields = ["codigo", "programado_por"]

    # -- Validaciones de un solo campo -------------------------------------

    def validate_fecha(self, value):
        """Al programar un partido nuevo la fecha tiene que estar por delante."""
        hoy = datetime.date.today()
        if self.instance is None and value < hoy:
            raise serializers.ValidationError(
                "No se puede programar un partido en una fecha pasada."
            )
        if value > hoy + datetime.timedelta(days=DIAS_MAXIMOS_A_FUTURO):
            raise serializers.ValidationError(
                f"No se puede programar con mas de {DIAS_MAXIMOS_A_FUTURO} dias de anticipacion."
            )
        return value

    def validate_jornada(self, value):
        if value < 1 or value > 60:
            raise serializers.ValidationError("La jornada debe estar entre 1 y 60.")
        return value

    def validate_estado(self, value):
        """
        La maquina de estados: de programado se avanza, nunca se retrocede.
        """
        if self.instance and value != self.instance.estado:
            permitidas = TRANSICIONES.get(self.instance.estado, [])
            if value not in permitidas:
                if not permitidas:
                    raise serializers.ValidationError(
                        f"Un partido '{self.instance.estado}' ya no cambia de estado."
                    )
                raise serializers.ValidationError(
                    f"Transicion no permitida: {self.instance.estado} -> {value}. "
                    f"Las validas son: {', '.join(permitidas)}."
                )
        return value

    # -- Validacion cruzada -------------------------------------------------

    def validate(self, attrs):
        def dato(nombre):
            """Valor nuevo si vino en el body, si no el que ya tiene el partido."""
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

        # 1. Un equipo no juega contra si mismo.
        if local and visitante and local == visitante:
            errores["equipo_visitante"] = (
                "El equipo visitante debe ser distinto del local."
            )

        # 2. Los dos equipos tienen que competir en la liga del partido.
        if liga:
            if local and local.liga_id != liga.id:
                errores["equipo_local"] = (
                    f"{local.nombre} no participa en {liga.nombre}."
                )
            if visitante and visitante.liga_id != liga.id:
                errores["equipo_visitante"] = (
                    f"{visitante.nombre} no participa en {liga.nombre}."
                )

        # 3. El resultado solo existe si el partido se jugo.
        hay_goles = goles_local is not None or goles_visitante is not None
        if estado == "jugado":
            if goles_local is None or goles_visitante is None:
                errores["goles_local"] = (
                    "Para marcar el partido como jugado hay que cargar ambos marcadores."
                )
        elif hay_goles:
            errores["goles_local"] = (
                f"Un partido '{estado}' no puede tener marcador cargado."
            )

        # Las reglas de agenda solo aplican mientras el partido ocupe la cancha.
        if estado not in ("programado", "jugado"):
            if errores:
                raise serializers.ValidationError(errores)
            return attrs

        # 4. El estadio tiene que estar libre en esa franja.
        if estadio and fecha and hora:
            libres = DisponibilidadService.estadios_libres(
                fecha, hora, excluir_partido=self.instance
            )
            if not libres.filter(pk=estadio.pk).exists():
                errores["estadio"] = (
                    f"{estadio.nombre} ya tiene un partido cerca de ese horario "
                    f"el {fecha}."
                )

        # 5. Ningun equipo juega dos partidos el mismo dia.
        if fecha:
            ocupados = DisponibilidadService.equipos_ocupados(
                fecha, excluir_partido=self.instance
            )
            if local and local.id in ocupados:
                errores.setdefault(
                    "equipo_local", f"{local.nombre} ya tiene un partido el {fecha}."
                )
            if visitante and visitante.id in ocupados:
                errores.setdefault(
                    "equipo_visitante",
                    f"{visitante.nombre} ya tiene un partido el {fecha}.",
                )

        if errores:
            raise serializers.ValidationError(errores)
        return attrs


class ResenaSerializer(serializers.ModelSerializer):
    autor_username = serializers.CharField(source="autor.username", read_only=True)
    partido_codigo = serializers.CharField(source="partido.codigo", read_only=True)

    class Meta:
        model = ResenaModel
        fields = [
            "id",
            "partido",
            "partido_codigo",
            "autor",
            "autor_username",
            "comentario",
            "puntuacion",
            "estado",
            "created_at",
        ]
        # El autor sale del token, nunca del body.
        read_only_fields = ["autor"]

    def validate_puntuacion(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La puntuacion va del 1 al 5.")
        return value

    def validate_comentario(self, value):
        comentario = value.strip()
        if len(comentario) < 10:
            raise serializers.ValidationError(
                "El comentario debe tener al menos 10 caracteres."
            )
        return comentario

    def validate_partido(self, value):
        """Solo se opina de un partido que ya se jugo."""
        if value.estado != "jugado":
            raise serializers.ValidationError(
                "Solo se pueden resenar partidos ya jugados."
            )
        return value

    def validate_estado(self, value):
        """Publicar u ocultar una resena es tarea del administrador."""
        request = self.context.get("request")
        if request and self.instance and value != self.instance.estado:
            usuario = request.user
            if not (usuario.rol == "admin" or usuario.is_superuser):
                raise serializers.ValidationError(
                    "Solo el administrador puede moderar el estado de una resena."
                )
        return value

    def validate(self, attrs):
        """Un usuario deja una sola resena por partido."""
        request = self.context.get("request")
        partido = attrs.get("partido", getattr(self.instance, "partido", None))

        if request and partido and self.instance is None:
            repetida = ResenaModel.objects.filter(
                partido=partido, autor=request.user
            ).exists()
            if repetida:
                raise serializers.ValidationError(
                    {"partido": "Ya dejaste una resena para este partido."}
                )
        return attrs


class TablaPosicionesSerializer(serializers.Serializer):
    """Solo documenta la respuesta de la tabla en Swagger; no toca la base."""

    posicion = serializers.IntegerField()
    equipo_id = serializers.IntegerField()
    equipo = serializers.CharField()
    escudo_url = serializers.CharField(allow_null=True)
    puntos = serializers.IntegerField()
    jugados = serializers.IntegerField()
    ganados = serializers.IntegerField()
    empatados = serializers.IntegerField()
    perdidos = serializers.IntegerField()
    goles_favor = serializers.IntegerField()
    goles_contra = serializers.IntegerField()
    diferencia_goles = serializers.IntegerField()
