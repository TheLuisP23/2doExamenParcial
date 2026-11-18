# 001 · Servicio A — plan técnico

## Stack
| Pieza | Elección | Motivo |
|---|---|---|
| Runtime | Python 3.12 | requisito |
| Gestor | `uv` (lockfile `uv.lock`) | instalaciones reproducibles y rápidas |
| Web | FastAPI + Uvicorn | requisito; OpenAPI nativo |
| Validación | Pydantic v2 (`extra="forbid"`) | REQ-A-007 |
| Config | `pydantic-settings` (prefijo `SERVICE_A_`) | REQ-SYS-005 |
| ORM / SQL | SQLAlchemy 2.x (Core + ORM, sync) + `psycopg` 3 | maduro, tipado |
| Migraciones | Alembic | REQ-A-012 |
| Logs | `structlog` → JSON a stdout | REQ-SYS-004 |
| Lint/format | `ruff` (lint + format) | — |
| Tipos | `mypy --strict` | NFR-A-005 |
| Pruebas | `pytest`, `pytest-cov`, `httpx`, `testcontainers[postgres]`, `schemathesis` | ver estrategia |

## Estructura y capas
```
services/service-a/
├── pyproject.toml · uv.lock · Dockerfile · alembic.ini · README.md
├── src/books/
│   ├── main.py              # app factory create_app(settings) + entrypoint
│   ├── config.py            # Settings (pydantic-settings), falla rápido
│   ├── logging.py           # structlog JSON + middleware request-id
│   ├── api/                 # CAPA API: routers, esquemas HTTP, problem+json handlers
│   │   ├── health.py · books.py · errors.py · schemas.py
│   ├── domain/              # CAPA DOMINIO: entidades, value objects, reglas, puertos
│   │   ├── book.py · isbn.py · errors.py · ports.py (BookRepository Protocol)
│   │   └── service.py       # casos de uso (create/get/list/replace/delete)
│   └── repository/          # CAPA REPOSITORIO: adaptador SQLAlchemy del puerto
│       ├── db.py · models.py · sql_book_repository.py
│       └── migrations/      # Alembic (env.py, versions/)
└── tests/
    ├── unit/                # dominio + API con repositorio en memoria
    ├── integration/         # repositorio + migraciones + app con PostgreSQL (Testcontainers)
    └── contract/            # schemathesis contra specs/001-servicio-a/contracts/openapi.yaml
```
Reglas de dependencia: `api → domain ← repository`. El dominio no importa FastAPI ni SQLAlchemy
(comprobado por una prueba de arquitectura en `tests/unit/test_layers.py`).

## Flujo de una petición
`Nginx /api/a/books` → (strip) → `FastAPI /books` → router `api/books.py` (valida con Pydantic)
→ `domain/service.py` (reglas, ISBN) → `BookRepository` (puerto) → `SqlBookRepository` → PostgreSQL.
Errores de dominio (`BookNotFound`, `DuplicateIsbn`, `InvalidBook`) se traducen a problem+json en `api/errors.py`.

## Configuración (variables de entorno)
| Variable | Obligatoria | Default | Uso |
|---|---|---|---|
| `SERVICE_A_DATABASE_URL` | sí | — | DSN SQLAlchemy `postgresql+psycopg://...` |
| `SERVICE_A_PORT` | no | `8000` | puerto HTTP |
| `SERVICE_A_LOG_LEVEL` | no | `INFO` | nivel de log |
| `SERVICE_A_DB_POOL_SIZE` | no | `5` | pool de conexiones |
| `SERVICE_A_READY_TIMEOUT_S` | no | `2` | timeout de readiness |

Arranque del contenedor: `alembic upgrade head && uvicorn books.main:app --host 0.0.0.0 --port $SERVICE_A_PORT`.

## Estrategia de pruebas
| Nivel | Herramienta | Alcance | Comando (lo ejecuta `make verify`) |
|---|---|---|---|
| Unitarias | pytest | dominio (ISBN, reglas), API con repo en memoria, config, logging | `uv run pytest tests/unit --cov=books --cov-fail-under=80` |
| Integración | pytest + Testcontainers (`postgres:16-alpine`) | repositorio, migraciones up/down, readiness real | `uv run pytest tests/integration` |
| Contrato | schemathesis (Python API, `from_path`) | todas las operaciones del `openapi.yaml` contra la app con BD Testcontainers | `uv run pytest tests/contract` |
| E2E | Playwright (en `frontend/e2e`) | flujos de UI que usan A | `make e2e` |
| Smoke post-deploy | `tests/smoke` | `/api/a/health/ready` en EKS | `make smoke URL=...` |

Convención de trazabilidad: cada test lleva `@pytest.mark.req("REQ-A-00X")` (marcador registrado en `pyproject.toml`).
La cobertura combinada unit+integration debe ser ≥ 80 %.

## Decisiones locales
- **Síncrono** (SQLAlchemy sync + threadpool de FastAPI): simplicidad académica; suficiente para la carga esperada.
- **PUT completo** en vez de PATCH: contrato más simple (Fuera de alcance: actualizaciones parciales).
- **Borrado físico**: no hay auditoría en alcance.
