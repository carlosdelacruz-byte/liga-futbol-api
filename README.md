# LigaApp API ⚽

API REST para la gestión de una liga de fútbol: ligas, equipos, estadios, jugadores,
usuarios con JWT y programación de partidos con control real de disponibilidad.

**Documentación interactiva:** `/docs/` · **Esquema OpenAPI:** `/schema/`

---

## Stack

| Componente | Tecnología |
|---|---|
| Framework | Django 5.2 + Django REST Framework |
| ORM | Django ORM |
| Base de datos | PostgreSQL |
| Autenticación | JWT (`djangorestframework-simplejwt`) |
| Documentación | Swagger / OpenAPI 3 (`drf-spectacular`) |
| Panel admin | Django Admin + Jazzmin |
| Despliegue | Render (Gunicorn + WhiteNoise) |

---

## Arquitectura

El proyecto está partido en **cuatro aplicaciones**, una por dominio. Cada una es
dueña de sus modelos, y las relaciones que cruzan de app se declaran por string
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
- PostgreSQL 14 o superior

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

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

### 3. Configurar las variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con los datos de la base de datos:

```
DB_NAME=liga_futbol
DB_USER=postgres
DB_PASSWORD=tu_clave
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=disable
```

> `DB_SSLMODE` va en `disable` para un Postgres local y en `require` en Render.

### 4. Migrar y crear el superusuario

```bash
python manage.py migrate
```

```bash
python manage.py createsuperuser
```

### 5. Levantar el servidor

```bash
python manage.py runserver
```

- API y Swagger: `http://127.0.0.1:8000/docs/`
- Panel de administración: `http://127.0.0.1:8000/admin/`

### 6. Cargar los datos de prueba

Desde el panel de administración, en este orden (cada uno depende del anterior):

1. **Liga** — por ejemplo *Liga 1 Perú*, temporada `2025-2026`
2. **Equipos** — asignados a esa liga
3. **Estadios** — uno por equipo
4. **Posiciones** — Arquero (ARQ), Defensa (DEF), Mediocampista (MED), Delantero (DEL)
5. **Jugadores** — con su equipo y posición
6. **Partidos** — o desde la propia API, que valida las reglas de negocio

Para probar los tres roles, creá tres usuarios desde el admin y asignales
`rol` = `admin`, `dt` y `hincha`. El registro público siempre crea hinchas,
a propósito.

---

## Autenticación

La API usa **JWT**. El flujo es siempre el mismo:

**1. Registrarse** — `POST /api/v1/auth/registro/`

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
{ "username": "admin", "password": "tu_clave" }
```

Respuesta:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**3. Usar el token** en cada petición:

```
Authorization: Bearer <access>
```

El `access` dura 30 minutos; cuando vence se pide uno nuevo con el `refresh`
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
| Editar la reseña de otro | **401** | **404** | **404** | 200 |

El **403 del hincha en un POST es la prueba** de que la API distingue roles:
primero demuestra quién es (JWT), después se evalúa qué puede hacer (permisos).

Los permisos se escriben una sola vez en `usuarios/permissions.py`
(`EsAdmin`, `EsAdminOrReadOnly`, `EsStaffDeLigaOrReadOnly`) y se reutilizan en
todas las vistas. Para lo que es "de cada uno" (reseñas, ficha propia) el filtro
va en `get_queryset()`: si el registro no es tuyo, ni siquiera está en tu
queryset y la API responde 404.

---

## Endpoints

Todo cuelga de `/api/v1/`. Son **22 rutas y 56 operaciones** documentadas.

### Autenticación
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro/` | Alta pública (nace con rol `hincha`) |
| POST | `/auth/login/` | Devuelve `access` + `refresh` |
| POST | `/auth/login/refresh/` | Renueva el `access` |

### Usuarios
| Método | Ruta | Descripción |
|---|---|---|
| GET, POST | `/usuarios/` | Padrón completo (solo admin) |
| GET, PUT, PATCH, DELETE | `/usuarios/{id}/` | Ficha del usuario (DELETE = baja lógica) |
| GET, PUT, PATCH | `/usuarios/perfil/` | El usuario que trae el token |

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
fecha**, porque la disponibilidad solo mira los `programado` y `jugado`. Un
partido ya `jugado` no se puede cancelar.

**Concurrencia.** El código público (`PAR-0001`) se asigna dentro de una
transacción con `select_for_update`: si dos personas programan partidos al mismo
tiempo, ninguna pisa el código de la otra.

### Jugadores

- Dorsal entre 1 y 99, **único dentro del equipo** (el mismo número sí puede repetirse en otro club).
- Edad entre 15 y 50 años; la fecha de nacimiento no puede ser futura.
- Altura entre 140 cm y 220 cm.
- Tope de 30 jugadores activos por plantel.
- `DELETE` es baja lógica: el jugador queda inactivo pero no se borra, porque aparece en partidos ya jugados.

### Ligas y equipos

- La temporada se escribe `AAAA-AAAA` y los años deben ser **consecutivos**.
- El año de fundación va de 1857 (el primer club del mundo) al año en curso.
- No se repite el nombre de equipo dentro de una misma liga.
- No se inscriben equipos en una liga inactiva.
- Un estadio profesional necesita entre 500 y 200.000 localidades.

### Reseñas

- Solo se opina de un partido **ya jugado**.
- Una reseña por usuario y partido.
- Puntuación de 1 a 5, comentario de 10 caracteres o más.
- El autor sale del token, nunca del body.
- Publicar u ocultar una reseña es tarea exclusiva del admin.

---

## Tabla de posiciones

`GET /api/v1/partidos/tabla/{liga_id}/` arma la tabla con los partidos jugados.

`TablaPosicionesService` arranca con todos los equipos de la liga en cero y
recorre los partidos en estado `jugado` **una sola vez**: cada partido suma para
su local y para su visitante en la misma pasada. Se dan 3 puntos por victoria y
1 por empate, y los desempates van por diferencia de gol y luego por goles a favor.

```json
[
  {
    "posicion": 1,
    "equipo": "Alianza Lima",
    "puntos": 9,
    "jugados": 3, "ganados": 3, "empatados": 0, "perdidos": 0,
    "goles_favor": 6, "goles_contra": 1, "diferencia_goles": 5
  }
]
```

---

## Despliegue en Render

El repositorio trae `render.yaml`, así que Render puede crear el servicio web y
la base de datos solos con **New → Blueprint**.

### Manual, paso a paso

**1. Crear la base de datos**
New → PostgreSQL → plan *Free* → Create. Anotar los datos de conexión.

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
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | los del paso 1 |
| `DB_SSLMODE` | `require` |
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

Y desde ahí cargar los datos por el panel `/admin/`.

### Qué hace cada archivo del despliegue

| Archivo | Para qué |
|---|---|
| `build.sh` | Instala dependencias, junta estáticos y migra en cada deploy |
| `render.yaml` | Describe el servicio y la base de datos como código |
| `runtime.txt` | Fija la versión de Python |
| `requirements.txt` | Dependencias con versión exacta, en UTF-8 |
| `.gitattributes` | Fuerza saltos de línea LF en `build.sh` |

> **Ojo con `build.sh`:** tiene que estar marcado como ejecutable en Git.
> Si Render responde `permission denied`, correr una vez:
> `git update-index --chmod=+x build.sh` y volver a hacer push.

---

## Decisiones de diseño

**Por qué los permisos van vista por vista.** Cada vista declara su
`permission_classes`, así se lee de un vistazo quién puede hacer qué sin tener
que ir a buscar una configuración global.

**Por qué bajas lógicas y no borrados.** Un partido jugado es historia: si se
borra, la tabla de posiciones deja de cuadrar. Lo mismo con los jugadores, que
aparecen en partidos ya disputados. Se marcan como cancelados o inactivos, y
las consultas los filtran.

**Por qué la propiedad se resuelve en `get_queryset()` y no en el permiso.**
Si el registro no es tuyo, directamente no está en tu queryset: la API responde
404 en vez de 403, y así ni siquiera confirma que ese id existe.

**Por qué las dos vistas `APIView` llevan `@extend_schema`.** La disponibilidad
y la tabla de posiciones no salen de un modelo, así que drf-spectacular no puede
adivinar qué devuelven y las dejaría **fuera de Swagger**. El decorador le dice
a mano qué documentar.

**Por qué `DURACION_PARTIDO_MINUTOS` vive en `utils/`.** La usan el servicio de
disponibilidad y, a través de él, el serializer. Es una regla del negocio, no un
detalle de ninguna de las dos.
