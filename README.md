# LabTrack · Del prompt al despliegue

LabTrack es una bitácora web de proyectos y experimentos de análisis de datos. Usa HTML, CSS y JavaScript en el navegador, FastAPI como API, SQLAlchemy para la persistencia y PostgreSQL como base de datos.

## Qué hace

- Autenticación con contraseñas protegidas, sesiones revocables, cookies HttpOnly y protección CSRF.
- Proyectos con operaciones de creación, consulta, edición y eliminación.
- Experimentos asociados a proyectos, con modelo, versión del dataset, métrica, valor, notas y estado.
- Aislamiento por usuario: cada usuario solo puede consultar y modificar sus propios proyectos y experimentos.
- Filtros exactos por nombre de modelo y status dentro del proyecto seleccionado; pueden combinarse.
- Resumen de proyectos y experimentos propios.
- Persistencia en PostgreSQL mediante SQLAlchemy y migraciones Alembic.
- Estados de experimento: `planned`, `completed` y `discarded`.

La documentación de requisitos, arquitectura, ERD y API está en [docs/02-arquitectura.md](docs/02-arquitectura.md).

## Inicio recomendado: Docker + PostgreSQL

Usa Python 3.11 o superior y Docker Desktop con el motor Linux disponible. Ejecuta los comandos desde la raíz del proyecto.

```bash
python scripts/init_env.py
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec app python -m app.cli seed-demo
```

Abre [http://127.0.0.1:8010](http://127.0.0.1:8010) en el navegador.

El comando `init_env.py` crea el archivo `.env` local con secretos generados. La contraseña de las cuentas demo se consulta en el valor `DEMO_PASSWORD` de ese archivo local. Nunca subas `.env`, contraseñas, tokens ni cookies a Git.

Para detener el despliegue local:

```bash
docker compose down
```

El despliegue actual está limitado a `127.0.0.1:8010`. GitHub almacena el código y ejecuta la integración continua; no publica automáticamente la aplicación.

## Migraciones

Alembic mantiene la evolución del esquema:

- `0001_initial`: crea las tablas iniciales de usuarios, sesiones, proyectos y experimentos.
- `0002_add_experiment_status`: agrega `Experiment.status` sin eliminar experimentos existentes. Las filas anteriores reciben el valor `completed`.

Las migraciones se ejecutan automáticamente en el servicio `migrate` antes de iniciar `app`. Para ejecutar una actualización manual en un entorno preparado:

```bash
python -m alembic upgrade head
```

No elimines la base de datos ni el volumen para resolver un error de migración. Conserva los datos y corrige la causa de la migración pendiente.

## Pruebas

Comprobaciones locales:

```bash
python -m pytest -q
python -m ruff check .
```

Pruebas aisladas con SQLite y PostgreSQL mediante Docker Compose:

```bash
docker compose --profile test run --build --rm tests
docker compose --profile test stop test-db
```

La suite cubre autenticación, cierre y revocación de sesión, CSRF, origen permitido, validación, CRUD, permisos entre usuarios, filtros, resumen, persistencia y migraciones repetibles.

## Reproducibilidad

Una copia limpia desde GitHub debe ejecutar `python scripts/init_env.py` para generar su propio `.env`.

Si se valida una segunda copia en la misma computadora, conviene usar un nombre de proyecto de Docker Compose diferente para aislar sus contenedores, red y volumen PostgreSQL:

```bash
docker compose -p labtrack-clean up -d --build --wait
docker compose -p labtrack-clean exec app python -m app.cli seed-demo
```

De esta manera la instalación limpia utiliza una base PostgreSQL independiente y comienza únicamente con los datos creados por `seed-demo`; no comparte registros ni secretos con la instalación original.

## Integración continua

GitHub Actions ejecuta CI para Python 3.11 y 3.12. Cada matriz levanta un servicio PostgreSQL de prueba, instala las dependencias, ejecuta Ruff y la suite de pytest, valida la configuración de Docker Compose y construye la imagen de la aplicación.

## Arquitectura

El navegador envía peticiones HTTP y JSON a la API. FastAPI valida los datos y la sesión, aplica los permisos del propietario y delega la persistencia en SQLAlchemy. PostgreSQL conserva los registros entre reinicios del proceso y de los contenedores mientras se mantenga el volumen.

El proyecto no ejecuta modelos de aprendizaje automático ni sube archivos: registra resultados y contexto de experimentos para consultarlos posteriormente.
