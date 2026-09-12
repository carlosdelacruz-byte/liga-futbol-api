import datetime

from django.db import migrations

EQUIPOS = [
    ("Alianza Lima", "Lima", 1901, "Estadio Alejandro Villanueva", 35000),
    ("Universitario", "Lima", 1924, "Estadio Monumental", 80000),
    ("Sporting Cristal", "Lima", 1955, "Estadio Alberto Gallardo", 18000),
    ("Melgar", "Arequipa", 1915, "Estadio Monumental de la UNSA", 60000),
    ("Cienciano", "Cusco", 1901, "Estadio Garcilaso de la Vega", 42000),
    ("Cesar Vallejo", "Trujillo", 1996, "Estadio Mansiche", 25000),
]

POSICIONES = [
    ("Arquero", "ARQ", "Defiende el arco"),
    ("Defensa", "DEF", "Ultima linea antes del arquero"),
    ("Mediocampista", "MED", "Conecta la defensa con el ataque"),
    ("Delantero", "DEL", "Encargado de convertir"),
]

PLANTEL = [
    ("Pedro", "Gallese", 1, "ARQ", 1990),
    ("Luis", "Advincula", 2, "DEF", 1990),
    ("Carlos", "Zambrano", 3, "DEF", 1989),
    ("Miguel", "Trauco", 4, "DEF", 1992),
    ("Alexander", "Callens", 5, "DEF", 1992),
    ("Renato", "Tapia", 6, "MED", 1995),
    ("Yoshimar", "Yotun", 7, "MED", 1990),
    ("Christian", "Cueva", 8, "MED", 1991),
    ("Sergio", "Pena", 9, "MED", 1995),
    ("Gianluca", "Lapadula", 10, "DEL", 1990),
    ("Andre", "Carrillo", 11, "DEL", 1991),
]

PARTIDOS_JUGADOS = [
    (0, 1, 2, 1, 21, 1),
    (2, 3, 3, 3, 20, 1),
    (4, 5, 0, 2, 19, 1),
    (1, 2, 1, 0, 14, 2),
    (3, 4, 2, 2, 13, 2),
    (5, 0, 1, 3, 12, 2),
]

PARTIDOS_PROGRAMADOS = [
    (0, 2, 7, 3),
    (3, 5, 8, 3),
    (1, 4, 9, 3),
]


def sembrar(apps, schema_editor):
    Liga = apps.get_model("ligas", "LigaModel")
    Equipo = apps.get_model("ligas", "EquipoModel")
    Estadio = apps.get_model("ligas", "EstadioModel")
    Posicion = apps.get_model("jugadores", "PosicionModel")
    Jugador = apps.get_model("jugadores", "JugadorModel")
    Partido = apps.get_model("partidos", "PartidoModel")

    if Liga.objects.exists():
        return

    ahora = datetime.datetime.now()
    hoy = datetime.date.today()

    liga = Liga.objects.create(
        nombre="Liga 1 Peru",
        temporada="2025-2026",
        pais="Peru",
        activa=True,
        created_at=ahora,
        updated_at=ahora,
    )

    posiciones = {}
    for nombre, abreviatura, descripcion in POSICIONES:
        posiciones[abreviatura] = Posicion.objects.create(
            nombre=nombre,
            abreviatura=abreviatura,
            descripcion=descripcion,
            created_at=ahora,
            updated_at=ahora,
        )

    equipos = []
    estadios = []
    for nombre, ciudad, fundacion, nombre_estadio, capacidad in EQUIPOS:
        equipo = Equipo.objects.create(
            nombre=nombre,
            ciudad=ciudad,
            fundacion=fundacion,
            activo=True,
            liga=liga,
            created_at=ahora,
            updated_at=ahora,
        )
        equipos.append(equipo)
        estadios.append(
            Estadio.objects.create(
                nombre=nombre_estadio,
                ciudad=ciudad,
                capacidad=capacidad,
                equipo=equipo,
                created_at=ahora,
                updated_at=ahora,
            )
        )

        for nombres, apellidos, dorsal, abreviatura, anio in PLANTEL:
            Jugador.objects.create(
                nombres=nombres,
                apellidos=apellidos,
                dorsal=dorsal,
                fecha_nacimiento=datetime.date(anio, 6, 15),
                nacionalidad="Peruana",
                altura_cm=178,
                pie_habil="derecho",
                activo=True,
                equipo=equipo,
                posicion=posiciones[abreviatura],
                created_at=ahora,
                updated_at=ahora,
            )

    numero = 1
    for local, visita, goles_local, goles_visita, dias_atras, jornada in PARTIDOS_JUGADOS:
        Partido.objects.create(
            liga=liga,
            equipo_local=equipos[local],
            equipo_visitante=equipos[visita],
            estadio=estadios[local],
            jornada=jornada,
            fecha=hoy - datetime.timedelta(days=dias_atras),
            hora=datetime.time(15, 30),
            estado="jugado",
            goles_local=goles_local,
            goles_visitante=goles_visita,
            codigo=f"PAR-{numero:04d}",
            created_at=ahora,
            updated_at=ahora,
        )
        numero += 1

    for local, visita, dias_adelante, jornada in PARTIDOS_PROGRAMADOS:
        Partido.objects.create(
            liga=liga,
            equipo_local=equipos[local],
            equipo_visitante=equipos[visita],
            estadio=estadios[local],
            jornada=jornada,
            fecha=hoy + datetime.timedelta(days=dias_adelante),
            hora=datetime.time(19, 0),
            estado="programado",
            codigo=f"PAR-{numero:04d}",
            created_at=ahora,
            updated_at=ahora,
        )
        numero += 1


def borrar(apps, schema_editor):
    for app, modelo in [
        ("partidos", "PartidoModel"),
        ("jugadores", "JugadorModel"),
        ("jugadores", "PosicionModel"),
        ("ligas", "EstadioModel"),
        ("ligas", "EquipoModel"),
        ("ligas", "LigaModel"),
    ]:
        apps.get_model(app, modelo).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("partidos", "0002_initial"),
        ("ligas", "0001_initial"),
        ("jugadores", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sembrar, borrar),
    ]
