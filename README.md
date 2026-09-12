# LigaApp API ⚽

API REST para la gestión de una liga de fútbol: ligas, equipos, estadios, jugadores,
usuarios con JWT y programación de partidos con control real de disponibilidad.

**Documentación interactiva:** `/docs/` · **Esquema OpenAPI:** `/schema/` · **ReDoc:** `/redoc/`

---

## Stack

| Componente | Tecnología |
|---|---|
| Framework | Django 5.2 + Django REST Framework |
| ORM | Django ORM |
| Base de datos | PostgreSQL |
| Autenticación | JWT (`djangorestframework-simplejwt`) |
| Documentación | Swagger / OpenAPI 3 (`drf-spectacular`) |
| Despliegue | Render (Gunicorn + WhiteNoise) |

---

## Arquitectura

El proyecto está partido en **cuatro aplicaciones**, una por dominio. Cada una es
dueña de sus modelos y las relaciones que cruzan de app se declaran por string
(`"ligas.EquipoModel"`), que es como Django resuelve dependencias entre módulos.

```
core/           configuración del proyecto y rutas raíz
├── ligas/          Liga → Equipo → Estadio      (la estructura del torneo)
├── jugadores/      Posición → Jugador            (los planteles)
├── usuarios/       Usuario + permisos por rol    (quién es quién)
├── partidos/       Partido → Reseña              (el fixture y la opinión)
└── utils/          código transversal (roles, envío de correo)
```

`utils/` no es una app: es el módulo común donde viven las constantes compartidas
y el helper de correo, que no le pertenecen a ningún dominio en particular.

### Modelo de datos

```
LigaModel ──< EquipoModel ──< EstadioModel
                  │                │
                  │                └──< PartidoModel >── LigaModel
                  ├──< JugadorModel >── PosicionModel
                  └──< UsuarioModel (equipo_favorito)
                                        │
                        PartidoModel ──< ResenaModel >── UsuarioModel
```

---

## Instalación local

### 1. Requisitos

- Python 3.12
- PostgreSQL 14 o superior (local, o una base en la nube)

### 2. Clonar e instalar

```bash
git clone <url-del-repositorio>
cd liga-futbol-api
python -m venv venv
```

Activar el entorno virtual:

```powershell
venv\Scripts\activate
```

```bash
source venv/bin/activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

### 3. Configurar las variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y poner la cadena de conexión de PostgreSQL en `DATABASE_URL`.
Toda la conexión viaja en una sola variable:

```
DATABASE_URL=postgresql://usuario:clave@localhost:5432/liga_futbol
```

### 4. Migrar y sembrar datos

```bash
python manage.py migrate
```

```bash
python manage.py sembrar_datos
```

El comando `sembrar_datos` carga una liga con 6 equipos, sus estadios, 66 jugadores,
6 partidos (3 jugados y 3 programados) y **tres usuarios de prueba, uno por rol**:

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin.LigaApp2026` | Administrador |
| `entrenador` | `Entrenador.2026` | Director técnico |
| `hincha` | `Hincha.2026` | Hincha |

### 5. Levantar el servidor

```bash
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/docs/`.

---

## Autenticación

La API usa **JWT**. El flujo es siempre el mismo:

**1. Registrarse** (o usar un usuario sembrado) — `POST /api/v1/auth/registro/`

```json
{
  "username": "nuevo_hincha",
  "email": "hincha@correo.com",
  "password": "Clave.Segura2026",
  "password_confirmacion": "Clave.Segura2026"
}
```

**2. Iniciar sesión** — `POST /api/v1/auth/login/`

```json
{ "username": "admin", "password": "Admin.LigaApp2026" }
```

La respuesta trae los dos tokens y los datos del usuario:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "usuario": { "id": 1, "username": "admin", "rol": "admin" }
}
```

**3. Usar el token** en cada petición:

```
Authorization: Bearer <access>
```

El `access` dura 60 minutos; cuando vence se pide uno nuevo con el `refresh`
(que dura 1 día) en `POST /api/v1/auth/login/refresh/`.

> En Swagger: botón **Authorize** (arriba a la derecha) → pegar `Bearer <access>`.

### Roles y permisos

| Acción | Sin token | Hincha | DT | Admin |
|---|---|---|---|---|
| Leer el catálogo | **401** | 200 | 200 | 200 |
| Crear ligas / equipos / estadios | **401** | **403** | **403** | **201** |
| Fichar jugadores | **401** | **403** | **201** | **201** |
| Programar partidos | **401** | **403** | **403** | **201** |
| Dejar una reseña | **401** | 201 | 201 | 201 |
| Moderar reseñas ajenas | **401** | **403** | **403** | 200 |

El **403 del hincha en un POST es la prueba** de que la API distingue roles:
primero demuestra quién es (JWT), después se evalúa qué puede hacer (permisos).

---

## Endpoints

Todo cuelga de `/api/v1/`. Son **24 rutas y 58 operaciones** documentadas.

### Autenticación
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro/` | Alta pública (nace con rol `hincha`) |
| POST | `/auth/login/` | Devuelve `access` + `refresh` |
| POST | `/auth/login/refresh/` | Renueva el `access` |
| POST | `/auth/login/verify/` | Valida un token |

### Usuarios
| Método | Ruta | Descripción |
|---|---|---|
| GET, POST | `/usuarios/` | Padrón completo (solo admin) |
| GET, PUT, PATCH, DELETE | `/usuarios/{id}/` | Ficha del usuario (DELETE = baja lógica) |
| GET, PUT, PATCH | `/usuarios/perfil/` | El usuario que trae el token |
| POST | `/usuarios/cambiar-password/` | Cambio de contraseña propia |

### Ligas, equipos y estadios
| Método | Ruta |
|---|---|
| GET, POST | `/ligas/` · `/equipos/` · `/estadios/` |
| GET, PUT, PATCH, DELETE | `/ligas/{id}/` · `/equipos/{id}/` · `/estadios/{id}/` |

### Jugadores
| Método | Ruta |
|---|---|
| GET, POST | `/posiciones/` · `/jugadores/` |
| GET, PUT, PATCH, DELETE | `/posiciones/{id}/` · `/jugadores/{id}/` |

### Partidos y reseñas
| Método | Ruta | Descripción |
|---|---|---|
| GET, POST | `/partidos/` | Fixture (POST genera el código `PAR-0001`) |
| GET, PUT, PATCH, DELETE | `/partidos/{id}/` | DELETE = cancelación (baja lógica) |
| GET | `/partidos/disponibilidad/` | Estadios libres en `?fecha=&hora=` |
| GET | `/partidos/tabla/{liga_id}/` | Tabla de posiciones calculada |
| GET, POST | `/resenas/` | Opinión sobre un partido jugado |
| GET, PUT, PATCH, DELETE | `/resenas/{id}/` | Solo el autor o el admin |

Todos los listados aceptan **filtros, búsqueda, orden y paginación**:

```
GET /api/v1/jugadores/?equipo=1&posicion=2&search=Guerrero&ordering=dorsal&page=2
```

---

## Reglas de negocio

Las validaciones viven **dentro de los serializers**, que es donde DRF espera
encontrarlas. Hay dos tipos: las de un campo (`validate_campo`) y las cruzadas
(`validate`), que necesitan mirar varios campos a la vez.

### Partidos — el núcleo

| Regla | Dónde |
|---|---|
| Un equipo no juega contra sí mismo | `PartidoSerializer.validate` |
| Los dos equipos deben competir en la liga del partido | `PartidoSerializer.validate` |
| El estadio debe estar libre en esa franja de 120 min | `validate` + `DisponibilidadService` |
| Ningún equipo juega dos partidos el mismo día | `validate` + `DisponibilidadService` |
| No se programa en una fecha pasada | `validate_fecha` |
| El marcador solo existe si el estado es `jugado` | `PartidoSerializer.validate` |
| Pasar a `jugado` exige cargar ambos marcadores | `PartidoSerializer.validate` |

**Máquina de estados.** Un partido avanza, nunca retrocede:

```
programado ──> jugado       (final, ya no se mueve)
     │    └──> suspendido ──> programado | cancelado
     └──────-> cancelado     (final, ya no se mueve)
```

**Baja lógica.** `DELETE /partidos/{id}/` no borra la fila: la marca `cancelado`
y responde 204. El partido queda en el historial pero **libera el estadio y la
fecha**, porque la disponibilidad solo mira los `programado` y `jugado`.

**Concurrencia.** El código público (`PAR-0001`) se asigna dentro de una
transacción con `select_for_update`: si dos personas programan partidos al mismo
tiempo, ninguna pisa el código de la otra.

### Jugadores

- Dorsal entre 1 y 99, **único dentro del equipo** (el mismo número sí puede repetirse en otro club).
- Edad entre 15 y 50 años; la fecha de nacimiento no puede ser futura.
- Tope de 30 jugadores activos por plantel.

### Ligas y equipos

- La temporada se escribe `AAAA-AAAA` y los años deben ser **consecutivos**.
- El año de fundación va de 1857 (el primer club del mundo) al año en curso.
- No se repite el nombre de equipo dentro de una misma liga.
- Un estadio profesional necesita al menos 500 localidades.

### Reseñas

- Solo se opina de un partido **ya jugado**.
- Una reseña por usuario y partido.
- Puntuación de 1 a 5, comentario de 10 caracteres o más.
- El autor sale del token, nunca del body.
- Publicar u ocultar una reseña es tarea exclusiva del admin.

---

## Tabla de posiciones

`GET /api/v1/partidos/tabla/{liga_id}/` arma la tabla con los partidos jugados.
El conteo se resuelve **en la base de datos** con agregaciones del ORM
(`Count` y `Sum` con `filter=Q(...)`), no trayendo los partidos a Python.

Se suman 3 puntos por victoria y 1 por empate, contando lo hecho de local y de
visitante. Los desempates van por diferencia de gol y luego por goles a favor.

```json
[
  {
    "posicion": 1,
    "equipo": "Alianza Lima",
    "puntos": 3,
    "jugados": 1, "ganados": 1, "empatados": 0, "perdidos": 0,
    "goles_favor": 2, "goles_contra": 1, "diferencia_goles": 1
  }
]
```

---

## Pruebas

```bash
python manage.py test
```

38 pruebas que cubren el registro y el login, los permisos por rol, todas las
validaciones de los serializers, la disponibilidad de estadios, la máquina de
estados y el cálculo de la tabla de posiciones.

---

## Despliegue en Render

El repositorio trae `render.yaml`, así que Render puede crear el servicio web y
la base de datos solos con **New → Blueprint**.

### Manual, paso a paso

**1. Crear la base de datos**
New → PostgreSQL → plan *Free* → Create. Copiar la **Internal Database URL**.

**2. Crear el servicio web**
New → Web Service → conectar el repositorio de GitHub.

| Campo | Valor |
|---|---|
| Runtime | Python 3 |
| Build Command | `./build.sh` |
| Start Command | `gunicorn core.wsgi:application` |

**3. Variables de entorno** (pestaña *Environment*)

| Clave | Valor |
|---|---|
| `DATABASE_URL` | la Internal Database URL del paso 1 |
| `SECRET_KEY` | una clave nueva (ver abajo) |
| `DEBUG` | `False` |
| `PYTHON_VERSION` | `3.12.10` |

Para generar la clave:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**4. Crear el superusuario** (pestaña *Shell*, una vez desplegado)

```bash
python manage.py createsuperuser
```

O sembrar todo de una:

```bash
python manage.py sembrar_datos
```

### Qué hace cada archivo del despliegue

| Archivo | Para qué |
|---|---|
| `build.sh` | Instala dependencias, junta estáticos y migra en cada deploy |
| `render.yaml` | Describe el servicio y la base de datos como código |
| `runtime.txt` | Fija la versión de Python |
| `requirements.txt` | Dependencias con versión exacta, en UTF-8 |

> **Ojo con `build.sh`:** tiene que estar marcado como ejecutable en Git.
> Si Render responde `permission denied`, correr una vez:
> `git update-index --chmod=+x build.sh` y volver a hacer push.

---

## Decisiones de diseño

**Por qué `DATABASE_URL` y no cinco variables sueltas.** Es el formato que
entrega Render y el que usa el resto del ecosistema. Una sola variable para
copiar y pegar, y el mismo `settings.py` sirve en local y en producción sin
tocar una línea.

**Por qué los permisos son restrictivos por defecto.** En `REST_FRAMEWORK` está
`DEFAULT_PERMISSION_CLASSES: IsAuthenticated`: todo pide token salvo que la
vista diga lo contrario. Olvidarse de proteger una vista deja el endpoint
cerrado, no abierto.

**Por qué bajas lógicas y no borrados.** Un partido jugado es historia: si se
borra, la tabla de posiciones deja de cuadrar. Lo mismo con los jugadores, que
aparecen en partidos ya disputados. Se marcan como cancelados o inactivos, y
las consultas los filtran.

**Por qué algunos serializers llevan `validators = []`.** DRF genera solo un
validador para cada `UniqueConstraint`, pero devuelve un mensaje genérico en
`non_field_errors`. Al apagarlo, nuestro `validate()` toma el control y
responde señalando el campo exacto (y compara sin distinguir mayúsculas, cosa
que la restricción de base de datos no hace). La restricción sigue en la base
como última línea de defensa.
