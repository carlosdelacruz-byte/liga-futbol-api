"""
Pruebas de las reglas de negocio del API.

No prueban a Django, prueban lo que escribimos nosotros: las validaciones
de los serializers, los permisos por rol y la tabla de posiciones.
"""

import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from jugadores.models import PosicionModel
from ligas.models import EquipoModel, EstadioModel, LigaModel
from partidos.models import PartidoModel
from usuarios.models import UsuarioModel


class BaseAPITestCase(APITestCase):
    """Arma una liga con cuatro equipos y los tres roles del sistema."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = UsuarioModel.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            password="Clave.Segura2026",
            rol="admin",
        )
        cls.dt = UsuarioModel.objects.create_user(
            username="dt_test",
            email="dt@test.com",
            password="Clave.Segura2026",
            rol="dt",
        )
        cls.hincha = UsuarioModel.objects.create_user(
            username="hincha_test",
            email="hincha@test.com",
            password="Clave.Segura2026",
            rol="hincha",
        )

        cls.liga = LigaModel.objects.create(
            nombre="Liga de Prueba", temporada="2025-2026", pais="Peru"
        )
        cls.otra_liga = LigaModel.objects.create(
            nombre="Liga Vecina", temporada="2025-2026", pais="Chile"
        )

        cls.equipo_a = EquipoModel.objects.create(
            nombre="Equipo A", ciudad="Lima", fundacion=1901, liga=cls.liga
        )
        cls.equipo_b = EquipoModel.objects.create(
            nombre="Equipo B", ciudad="Lima", fundacion=1924, liga=cls.liga
        )
        cls.equipo_c = EquipoModel.objects.create(
            nombre="Equipo C", ciudad="Cusco", fundacion=1955, liga=cls.liga
        )
        cls.equipo_forastero = EquipoModel.objects.create(
            nombre="Forastero", ciudad="Santiago", fundacion=1933, liga=cls.otra_liga
        )

        cls.estadio_a = EstadioModel.objects.create(
            nombre="Estadio A", ciudad="Lima", capacidad=30000, equipo=cls.equipo_a
        )
        cls.estadio_b = EstadioModel.objects.create(
            nombre="Estadio B", ciudad="Lima", capacidad=45000, equipo=cls.equipo_b
        )

        cls.posicion = PosicionModel.objects.create(nombre="Delantero", abreviatura="DEL")
        cls.manana = datetime.date.today() + datetime.timedelta(days=10)

    def autenticar(self, usuario):
        self.client.force_authenticate(user=usuario)


class AutenticacionTests(APITestCase):
    def test_registro_crea_usuario_con_rol_hincha(self):
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "nuevo_hincha",
                "email": "nuevo@test.com",
                "password": "Clave.Segura2026",
                "password_confirmacion": "Clave.Segura2026",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        usuario = UsuarioModel.objects.get(username="nuevo_hincha")
        self.assertEqual(usuario.rol, "hincha")
        self.assertFalse(usuario.is_staff)
        # La clave se guarda hasheada, nunca en texto plano.
        self.assertNotEqual(usuario.password, "Clave.Segura2026")
        self.assertNotIn("password", respuesta.data)

    def test_registro_rechaza_password_que_no_coincide(self):
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "descuidado",
                "email": "descuidado@test.com",
                "password": "Clave.Segura2026",
                "password_confirmacion": "Otra.Clave2026",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirmacion", respuesta.data)

    def test_registro_rechaza_email_repetido(self):
        UsuarioModel.objects.create_user(
            username="ocupado", email="repetido@test.com", password="Clave.Segura2026"
        )
        respuesta = self.client.post(
            reverse("registro"),
            {
                "username": "otro_usuario",
                "email": "repetido@test.com",
                "password": "Clave.Segura2026",
                "password_confirmacion": "Clave.Segura2026",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", respuesta.data)

    def test_login_devuelve_access_y_refresh(self):
        UsuarioModel.objects.create_user(
            username="logueado", email="log@test.com", password="Clave.Segura2026"
        )
        respuesta = self.client.post(
            reverse("login"),
            {"username": "logueado", "password": "Clave.Segura2026"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn("access", respuesta.data)
        self.assertIn("refresh", respuesta.data)
        self.assertEqual(respuesta.data["usuario"]["rol"], "hincha")


class PermisosTests(BaseAPITestCase):
    def test_sin_token_no_se_lee_el_catalogo(self):
        respuesta = self.client.get(reverse("equipos-list"))
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_hincha_lee_pero_no_escribe(self):
        self.autenticar(self.hincha)

        lectura = self.client.get(reverse("equipos-list"))
        self.assertEqual(lectura.status_code, status.HTTP_200_OK)

        escritura = self.client.post(
            reverse("equipos-list"),
            {
                "nombre": "Equipo Pirata",
                "ciudad": "Lima",
                "fundacion": 2000,
                "liga": self.liga.id,
            },
            format="json",
        )
        self.assertEqual(escritura.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_si_escribe(self):
        self.autenticar(self.admin)
        respuesta = self.client.post(
            reverse("equipos-list"),
            {
                "nombre": "Equipo Nuevo",
                "ciudad": "Piura",
                "fundacion": 2000,
                "liga": self.liga.id,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_dt_ficha_jugadores_pero_no_crea_equipos(self):
        self.autenticar(self.dt)

        jugador = self.client.post(
            reverse("jugadores-list"),
            {
                "nombres": "Nuevo",
                "apellidos": "Jugador",
                "dorsal": 9,
                "fecha_nacimiento": "2000-05-20",
                "nacionalidad": "Peruana",
                "equipo": self.equipo_a.id,
                "posicion": self.posicion.id,
            },
            format="json",
        )
        self.assertEqual(jugador.status_code, status.HTTP_201_CREATED)

        equipo = self.client.post(
            reverse("equipos-list"),
            {
                "nombre": "Equipo del DT",
                "ciudad": "Lima",
                "fundacion": 2000,
                "liga": self.liga.id,
            },
            format="json",
        )
        self.assertEqual(equipo.status_code, status.HTTP_403_FORBIDDEN)


class ValidacionesJugadorTests(BaseAPITestCase):
    def setUp(self):
        self.autenticar(self.admin)

    def _payload(self, **cambios):
        datos = {
            "nombres": "Jugador",
            "apellidos": "De Prueba",
            "dorsal": 10,
            "fecha_nacimiento": "1998-03-15",
            "nacionalidad": "Peruana",
            "equipo": self.equipo_a.id,
            "posicion": self.posicion.id,
        }
        datos.update(cambios)
        return datos

    def test_dorsal_fuera_de_rango(self):
        respuesta = self.client.post(
            reverse("jugadores-list"), self._payload(dorsal=100), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dorsal", respuesta.data)

    def test_dorsal_repetido_en_el_mismo_equipo(self):
        self.client.post(reverse("jugadores-list"), self._payload(), format="json")
        repetido = self.client.post(
            reverse("jugadores-list"), self._payload(), format="json"
        )
        self.assertEqual(repetido.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dorsal", repetido.data)

    def test_mismo_dorsal_en_otro_equipo_si_se_permite(self):
        self.client.post(reverse("jugadores-list"), self._payload(), format="json")
        otro = self.client.post(
            reverse("jugadores-list"),
            self._payload(equipo=self.equipo_b.id),
            format="json",
        )
        self.assertEqual(otro.status_code, status.HTTP_201_CREATED)

    def test_jugador_demasiado_joven(self):
        hace_diez_anios = datetime.date.today() - datetime.timedelta(days=365 * 10)
        respuesta = self.client.post(
            reverse("jugadores-list"),
            self._payload(fecha_nacimiento=hace_diez_anios.isoformat()),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_nacimiento", respuesta.data)

    def test_fecha_de_nacimiento_futura(self):
        futuro = datetime.date.today() + datetime.timedelta(days=30)
        respuesta = self.client.post(
            reverse("jugadores-list"),
            self._payload(fecha_nacimiento=futuro.isoformat()),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


class ValidacionesPartidoTests(BaseAPITestCase):
    def setUp(self):
        self.autenticar(self.admin)

    def _payload(self, **cambios):
        datos = {
            "liga": self.liga.id,
            "equipo_local": self.equipo_a.id,
            "equipo_visitante": self.equipo_b.id,
            "estadio": self.estadio_a.id,
            "jornada": 1,
            "fecha": self.manana.isoformat(),
            "hora": "19:00",
        }
        datos.update(cambios)
        return datos

    def test_programar_partido_genera_codigo(self):
        respuesta = self.client.post(
            reverse("partidos-list"), self._payload(), format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        partido = PartidoModel.objects.get(pk=respuesta.data["id"])
        self.assertEqual(partido.codigo, f"PAR-{partido.id:04d}")
        # El responsable sale del token, no del body.
        self.assertEqual(partido.programado_por, self.admin)

    def test_un_equipo_no_juega_contra_si_mismo(self):
        respuesta = self.client.post(
            reverse("partidos-list"),
            self._payload(equipo_visitante=self.equipo_a.id),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("equipo_visitante", respuesta.data)

    def test_equipo_de_otra_liga_es_rechazado(self):
        respuesta = self.client.post(
            reverse("partidos-list"),
            self._payload(equipo_visitante=self.equipo_forastero.id),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("equipo_visitante", respuesta.data)

    def test_fecha_pasada_es_rechazada(self):
        ayer = datetime.date.today() - datetime.timedelta(days=1)
        respuesta = self.client.post(
            reverse("partidos-list"),
            self._payload(fecha=ayer.isoformat()),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha", respuesta.data)

    def test_estadio_ocupado_en_la_misma_franja(self):
        self.client.post(reverse("partidos-list"), self._payload(), format="json")
        # Mismo estadio, una hora despues: cae dentro de los 120 minutos.
        choque = self.client.post(
            reverse("partidos-list"),
            self._payload(
                equipo_local=self.equipo_c.id,
                equipo_visitante=self.equipo_b.id,
                hora="20:00",
            ),
            format="json",
        )
        self.assertEqual(choque.status_code, status.HTTP_400_BAD_REQUEST)

    def test_un_equipo_no_juega_dos_veces_el_mismo_dia(self):
        self.client.post(reverse("partidos-list"), self._payload(), format="json")
        # Otro estadio y otro horario, pero el Equipo B repite fecha.
        repetido = self.client.post(
            reverse("partidos-list"),
            self._payload(
                equipo_local=self.equipo_c.id,
                equipo_visitante=self.equipo_b.id,
                estadio=self.estadio_b.id,
                hora="23:00",
            ),
            format="json",
        )
        self.assertEqual(repetido.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("equipo_visitante", repetido.data)

    def test_goles_sin_estado_jugado_es_rechazado(self):
        respuesta = self.client.post(
            reverse("partidos-list"),
            self._payload(goles_local=2, goles_visitante=1),
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("goles_local", respuesta.data)

    def test_pasar_a_jugado_exige_marcador(self):
        creado = self.client.post(
            reverse("partidos-list"), self._payload(), format="json"
        )
        detalle = reverse("partidos-detail", args=[creado.data["id"]])

        sin_goles = self.client.patch(detalle, {"estado": "jugado"}, format="json")
        self.assertEqual(sin_goles.status_code, status.HTTP_400_BAD_REQUEST)

        con_goles = self.client.patch(
            detalle,
            {"estado": "jugado", "goles_local": 2, "goles_visitante": 1},
            format="json",
        )
        self.assertEqual(con_goles.status_code, status.HTTP_200_OK)

    def test_transicion_invalida_no_vuelve_atras(self):
        creado = self.client.post(
            reverse("partidos-list"), self._payload(), format="json"
        )
        detalle = reverse("partidos-detail", args=[creado.data["id"]])
        self.client.patch(
            detalle,
            {"estado": "jugado", "goles_local": 1, "goles_visitante": 0},
            format="json",
        )
        # Un partido jugado ya no vuelve a programado.
        vuelta = self.client.patch(detalle, {"estado": "programado"}, format="json")
        self.assertEqual(vuelta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("estado", vuelta.data)

    def test_delete_es_baja_logica(self):
        creado = self.client.post(
            reverse("partidos-list"), self._payload(), format="json"
        )
        detalle = reverse("partidos-detail", args=[creado.data["id"]])

        borrado = self.client.delete(detalle)
        self.assertEqual(borrado.status_code, status.HTTP_204_NO_CONTENT)

        # El partido sigue existiendo, pero cancelado.
        consulta = self.client.get(detalle)
        self.assertEqual(consulta.status_code, status.HTTP_200_OK)
        self.assertEqual(consulta.data["estado"], "cancelado")

    def test_partido_cancelado_libera_el_estadio(self):
        creado = self.client.post(
            reverse("partidos-list"), self._payload(), format="json"
        )
        self.client.delete(reverse("partidos-detail", args=[creado.data["id"]]))

        # Con el anterior cancelado, el mismo estadio y fecha vuelven a estar libres.
        nuevo = self.client.post(
            reverse("partidos-list"), self._payload(), format="json"
        )
        self.assertEqual(nuevo.status_code, status.HTTP_201_CREATED)


class DisponibilidadTests(BaseAPITestCase):
    def setUp(self):
        self.autenticar(self.admin)

    def test_disponibilidad_exige_fecha_y_hora(self):
        respuesta = self.client.get(reverse("partidos-disponibilidad"))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_disponibilidad_descuenta_el_estadio_ocupado(self):
        url = reverse("partidos-disponibilidad")
        parametros = {"fecha": self.manana.isoformat(), "hora": "19:00"}

        antes = self.client.get(url, parametros)
        cantidad_antes = len(antes.data["estadios_libres"])

        self.client.post(
            reverse("partidos-list"),
            {
                "liga": self.liga.id,
                "equipo_local": self.equipo_a.id,
                "equipo_visitante": self.equipo_b.id,
                "estadio": self.estadio_a.id,
                "jornada": 1,
                "fecha": self.manana.isoformat(),
                "hora": "19:00",
            },
            format="json",
        )

        despues = self.client.get(url, parametros)
        self.assertEqual(len(despues.data["estadios_libres"]), cantidad_antes - 1)


class TablaPosicionesTests(BaseAPITestCase):
    def test_tabla_suma_puntos_y_ordena(self):
        hoy = datetime.date.today()
        # A le gana a B (3 puntos para A), C empata con B.
        PartidoModel.objects.create(
            liga=self.liga,
            equipo_local=self.equipo_a,
            equipo_visitante=self.equipo_b,
            estadio=self.estadio_a,
            fecha=hoy - datetime.timedelta(days=5),
            hora=datetime.time(16, 0),
            estado="jugado",
            goles_local=3,
            goles_visitante=0,
        )
        PartidoModel.objects.create(
            liga=self.liga,
            equipo_local=self.equipo_c,
            equipo_visitante=self.equipo_b,
            estadio=self.estadio_b,
            fecha=hoy - datetime.timedelta(days=3),
            hora=datetime.time(16, 0),
            estado="jugado",
            goles_local=1,
            goles_visitante=1,
        )

        self.autenticar(self.hincha)
        respuesta = self.client.get(reverse("partidos-tabla", args=[self.liga.id]))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        tabla = {fila["equipo"]: fila for fila in respuesta.data}
        self.assertEqual(tabla["Equipo A"]["puntos"], 3)
        self.assertEqual(tabla["Equipo A"]["diferencia_goles"], 3)
        self.assertEqual(tabla["Equipo B"]["puntos"], 1)
        self.assertEqual(tabla["Equipo C"]["puntos"], 1)
        # El lider encabeza la tabla.
        self.assertEqual(respuesta.data[0]["equipo"], "Equipo A")
        self.assertEqual(respuesta.data[0]["posicion"], 1)


class ResenaTests(BaseAPITestCase):
    def setUp(self):
        self.partido_jugado = PartidoModel.objects.create(
            liga=self.liga,
            equipo_local=self.equipo_a,
            equipo_visitante=self.equipo_b,
            estadio=self.estadio_a,
            fecha=datetime.date.today() - datetime.timedelta(days=2),
            hora=datetime.time(16, 0),
            estado="jugado",
            goles_local=1,
            goles_visitante=1,
        )
        self.partido_programado = PartidoModel.objects.create(
            liga=self.liga,
            equipo_local=self.equipo_c,
            equipo_visitante=self.equipo_a,
            estadio=self.estadio_b,
            fecha=self.manana,
            hora=datetime.time(16, 0),
            estado="programado",
        )

    def test_no_se_resena_un_partido_no_jugado(self):
        self.autenticar(self.hincha)
        respuesta = self.client.post(
            reverse("resenas-list"),
            {
                "partido": self.partido_programado.id,
                "comentario": "Todavia no se juega este partido.",
                "puntuacion": 5,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("partido", respuesta.data)

    def test_una_resena_por_usuario_y_partido(self):
        self.autenticar(self.hincha)
        datos = {
            "partido": self.partido_jugado.id,
            "comentario": "Gran partido, muy parejo de principio a fin.",
            "puntuacion": 4,
        }
        primera = self.client.post(reverse("resenas-list"), datos, format="json")
        self.assertEqual(primera.status_code, status.HTTP_201_CREATED)
        # El autor sale del token.
        self.assertEqual(primera.data["autor_username"], self.hincha.username)

        segunda = self.client.post(reverse("resenas-list"), datos, format="json")
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comentario_muy_corto(self):
        self.autenticar(self.hincha)
        respuesta = self.client.post(
            reverse("resenas-list"),
            {"partido": self.partido_jugado.id, "comentario": "malo", "puntuacion": 1},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("comentario", respuesta.data)

    def test_puntuacion_fuera_de_rango(self):
        self.autenticar(self.hincha)
        respuesta = self.client.post(
            reverse("resenas-list"),
            {
                "partido": self.partido_jugado.id,
                "comentario": "Un partido bastante entretenido.",
                "puntuacion": 9,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("puntuacion", respuesta.data)

    def test_solo_el_admin_modera_el_estado(self):
        self.autenticar(self.hincha)
        creada = self.client.post(
            reverse("resenas-list"),
            {
                "partido": self.partido_jugado.id,
                "comentario": "Buen encuentro, lo recomiendo.",
                "puntuacion": 5,
            },
            format="json",
        )
        detalle = reverse("resenas-detail", args=[creada.data["id"]])

        propia = self.client.patch(detalle, {"estado": "publicada"}, format="json")
        self.assertEqual(propia.status_code, status.HTTP_400_BAD_REQUEST)

        self.autenticar(self.admin)
        moderada = self.client.patch(detalle, {"estado": "publicada"}, format="json")
        self.assertEqual(moderada.status_code, status.HTTP_200_OK)

    def test_un_hincha_no_edita_la_resena_de_otro(self):
        self.autenticar(self.hincha)
        creada = self.client.post(
            reverse("resenas-list"),
            {
                "partido": self.partido_jugado.id,
                "comentario": "Comentario del primer hincha.",
                "puntuacion": 5,
            },
            format="json",
        )
        detalle = reverse("resenas-detail", args=[creada.data["id"]])

        intruso = UsuarioModel.objects.create_user(
            username="intruso", email="intruso@test.com", password="Clave.Segura2026"
        )
        self.autenticar(intruso)
        respuesta = self.client.patch(
            detalle, {"comentario": "Comentario cambiado por un tercero."}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


class ValidacionesLigaTests(BaseAPITestCase):
    def setUp(self):
        self.autenticar(self.admin)

    def test_temporada_con_formato_invalido(self):
        respuesta = self.client.post(
            reverse("ligas-list"),
            {"nombre": "Liga Nueva", "temporada": "2025", "pais": "Peru"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("temporada", respuesta.data)

    def test_temporada_con_anios_no_consecutivos(self):
        respuesta = self.client.post(
            reverse("ligas-list"),
            {"nombre": "Liga Nueva", "temporada": "2025-2030", "pais": "Peru"},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("temporada", respuesta.data)

    def test_equipo_con_fundacion_futura(self):
        anio_futuro = datetime.date.today().year + 1
        respuesta = self.client.post(
            reverse("equipos-list"),
            {
                "nombre": "Equipo del Futuro",
                "ciudad": "Lima",
                "fundacion": anio_futuro,
                "liga": self.liga.id,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fundacion", respuesta.data)

    def test_equipo_repetido_en_la_misma_liga(self):
        respuesta = self.client.post(
            reverse("equipos-list"),
            {
                "nombre": "Equipo A",
                "ciudad": "Lima",
                "fundacion": 1950,
                "liga": self.liga.id,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nombre", respuesta.data)

    def test_estadio_con_capacidad_muy_baja(self):
        respuesta = self.client.post(
            reverse("estadios-list"),
            {
                "nombre": "Canchita del barrio",
                "ciudad": "Lima",
                "capacidad": 50,
                "equipo": self.equipo_a.id,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacidad", respuesta.data)
