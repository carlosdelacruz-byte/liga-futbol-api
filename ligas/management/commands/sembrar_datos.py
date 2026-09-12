"""
Carga datos de ejemplo para poder probar el API apenas se despliega.

    python manage.py sembrar_datos

Es idempotente: se puede correr varias veces sin duplicar nada.
"""

import datetime
import random

from django.core.management.base import BaseCommand
from django.db import transaction

from jugadores.models import JugadorModel, PosicionModel
from ligas.models import EquipoModel, EstadioModel, LigaModel
from partidos.models import PartidoModel
from usuarios.models import UsuarioModel

POSICIONES = [
    ("Arquero", "ARQ", "Defiende el arco"),
    ("Defensa", "DEF", "Ultima linea antes del arquero"),
    ("Mediocampista", "MED", "Conecta la defensa con el ataque"),
    ("Delantero", "DEL", "Encargado de convertir"),
]

EQUIPOS = [
    ("Alianza Lima", "Lima", 1901, "Estadio Alejandro Villanueva", 35000),
    ("Universitario", "Lima", 1924, "Estadio Monumental", 80000),
    ("Sporting Cristal", "Lima", 1955, "Estadio Alberto Gallardo", 18000),
    ("Melgar", "Arequipa", 1915, "Estadio Monumental de la UNSA", 60000),
    ("Cienciano", "Cusco", 1901, "Estadio Garcilaso de la Vega", 42000),
    ("Cesar Vallejo", "Trujillo", 1996, "Estadio Mansiche", 25000),
]

NOMBRES = [
    "Luis", "Carlos", "Jefferson", "Paolo", "Andre", "Christian", "Miguel",
    "Renato", "Gianluca", "Alex", "Edison", "Wilder", "Yoshimar", "Sergio",
    "Bryan", "Piero", "Marcos", "Anderson", "Joao", "Franco",
]

APELLIDOS = [
    "Advincula", "Zambrano", "Farfan", "Guerrero", "Carrillo", "Cueva",
    "Trauco", "Tapia", "Lapadula", "Valera", "Flores", "Cartagena",
    "Yotun", "Pena", "Reyna", "Quispe", "Lopez", "Santamaria", "Grimaldo",
    "Concha",
]


class Command(BaseCommand):
    help = "Siembra ligas, equipos, estadios, jugadores, usuarios y partidos de ejemplo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reiniciar",
            action="store_true",
            help="Borra los datos sembrados antes de volver a crearlos.",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        random.seed(30)  # La misma semilla siempre genera el mismo plantel.

        if opciones["reiniciar"]:
            self.stdout.write("Limpiando datos anteriores...")
            PartidoModel.objects.all().delete()
            JugadorModel.objects.all().delete()
            EstadioModel.objects.all().delete()
            EquipoModel.objects.all().delete()
            LigaModel.objects.all().delete()
            PosicionModel.objects.all().delete()

        # --- Usuarios -----------------------------------------------------
        admin, creado = UsuarioModel.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@ligaapp.com",
                "rol": "admin",
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Administrador",
            },
        )
        if creado:
            admin.set_password("Admin.LigaApp2026")
            admin.save()
            self.stdout.write(self.style.SUCCESS("  Admin creado: admin / Admin.LigaApp2026"))

        dt, creado = UsuarioModel.objects.get_or_create(
            username="entrenador",
            defaults={"email": "dt@ligaapp.com", "rol": "dt", "first_name": "Director"},
        )
        if creado:
            dt.set_password("Entrenador.2026")
            dt.save()
            self.stdout.write(self.style.SUCCESS("  DT creado: entrenador / Entrenador.2026"))

        hincha, creado = UsuarioModel.objects.get_or_create(
            username="hincha",
            defaults={"email": "hincha@ligaapp.com", "rol": "hincha"},
        )
        if creado:
            hincha.set_password("Hincha.2026")
            hincha.save()
            self.stdout.write(self.style.SUCCESS("  Hincha creado: hincha / Hincha.2026"))

        # --- Posiciones ---------------------------------------------------
        posiciones = {}
        for nombre, abreviatura, descripcion in POSICIONES:
            posicion, _ = PosicionModel.objects.get_or_create(
                nombre=nombre,
                defaults={"abreviatura": abreviatura, "descripcion": descripcion},
            )
            posiciones[abreviatura] = posicion

        # --- Liga, equipos y estadios -------------------------------------
        liga, _ = LigaModel.objects.get_or_create(
            nombre="Liga 1 Peru",
            temporada="2025-2026",
            defaults={"pais": "Peru", "activa": True},
        )

        equipos = []
        for nombre, ciudad, fundacion, estadio_nombre, capacidad in EQUIPOS:
            equipo, _ = EquipoModel.objects.get_or_create(
                liga=liga,
                nombre=nombre,
                defaults={"ciudad": ciudad, "fundacion": fundacion},
            )
            EstadioModel.objects.get_or_create(
                equipo=equipo,
                nombre=estadio_nombre,
                defaults={"ciudad": ciudad, "capacidad": capacidad},
            )
            equipos.append(equipo)

        # --- Jugadores ----------------------------------------------------
        # Plantel de 11: 1 arquero, 4 defensas, 4 medios, 2 delanteros.
        reparto = ["ARQ"] + ["DEF"] * 4 + ["MED"] * 4 + ["DEL"] * 2
        creados = 0
        for equipo in equipos:
            if equipo.jugadores.exists():
                continue
            for dorsal, abreviatura in enumerate(reparto, start=1):
                JugadorModel.objects.create(
                    nombres=random.choice(NOMBRES),
                    apellidos=random.choice(APELLIDOS),
                    dorsal=dorsal,
                    fecha_nacimiento=datetime.date(
                        random.randint(1992, 2006),
                        random.randint(1, 12),
                        random.randint(1, 28),
                    ),
                    nacionalidad="Peruana",
                    altura_cm=random.randint(165, 192),
                    pie_habil=random.choice(["derecho", "izquierdo"]),
                    equipo=equipo,
                    posicion=posiciones[abreviatura],
                )
                creados += 1

        # --- Partidos -----------------------------------------------------
        # Jornada 1 ya jugada (para que la tabla de posiciones tenga datos)
        # y jornada 2 programada hacia adelante.
        if not PartidoModel.objects.exists():
            hoy = datetime.date.today()
            jornada_1 = hoy - datetime.timedelta(days=7)

            cruces_jugados = [
                (equipos[0], equipos[1], 2, 1),
                (equipos[2], equipos[3], 3, 3),
                (equipos[4], equipos[5], 0, 2),
            ]
            for indice, (local, visita, gl, gv) in enumerate(cruces_jugados):
                # Un dia distinto por cruce: dos equipos no juegan el mismo dia.
                partido = PartidoModel.objects.create(
                    liga=liga,
                    equipo_local=local,
                    equipo_visitante=visita,
                    estadio=local.estadios.first(),
                    jornada=1,
                    fecha=jornada_1 + datetime.timedelta(days=indice),
                    hora=datetime.time(15, 30),
                    estado="jugado",
                    goles_local=gl,
                    goles_visitante=gv,
                    programado_por=admin,
                )
                partido.codigo = f"PAR-{partido.id:04d}"
                partido.save(update_fields=["codigo"])

            jornada_2 = hoy + datetime.timedelta(days=7)
            cruces_programados = [
                (equipos[1], equipos[2]),
                (equipos[3], equipos[4]),
                (equipos[5], equipos[0]),
            ]
            for indice, (local, visita) in enumerate(cruces_programados):
                partido = PartidoModel.objects.create(
                    liga=liga,
                    equipo_local=local,
                    equipo_visitante=visita,
                    estadio=local.estadios.first(),
                    jornada=2,
                    fecha=jornada_2 + datetime.timedelta(days=indice),
                    hora=datetime.time(19, 0),
                    estado="programado",
                    programado_por=admin,
                )
                partido.codigo = f"PAR-{partido.id:04d}"
                partido.save(update_fields=["codigo"])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Datos sembrados:"))
        self.stdout.write(f"  Ligas:     {LigaModel.objects.count()}")
        self.stdout.write(f"  Equipos:   {EquipoModel.objects.count()}")
        self.stdout.write(f"  Estadios:  {EstadioModel.objects.count()}")
        self.stdout.write(f"  Jugadores: {JugadorModel.objects.count()}")
        self.stdout.write(f"  Partidos:  {PartidoModel.objects.count()}")
        self.stdout.write(f"  Usuarios:  {UsuarioModel.objects.count()}")
