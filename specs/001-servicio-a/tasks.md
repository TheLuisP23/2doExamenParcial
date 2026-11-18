# 001 · Servicio A — tareas

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md). Las pruebas preceden a la implementación.
> Todas las rutas son relativas a la raíz del repo. `make task-done` ejecuta `make verify` antes de marcar.

- [ ] **TASK-A-01** — Esqueleto del proyecto (tooling, sin lógica)
  - Tipo: scaffold
  - Depende de: —
  - REQ: —
  - Archivos: `services/service-a/pyproject.toml`, `services/service-a/uv.lock`, `services/service-a/README.md`, `services/service-a/src/books/__init__.py`, `services/service-a/src/books/py.typed`, `services/service-a/tests/__init__.py`, `services/service-a/tests/conftest.py`, `services/service-a/tests/unit/__init__.py`, `services/service-a/tests/integration/__init__.py`, `services/service-a/tests/contract/__init__.py`, `services/service-a/.python-version`
  - Hecho cuando: `uv sync` instala; `ruff check`, `ruff format --check` y `mypy --strict src` pasan; marcador `req` registrado; `make verify` verde.

- [ ] **TASK-A-02** — Pruebas: config, logging, health
  - Tipo: test
  - Depende de: TASK-A-01
  - REQ: REQ-A-008, REQ-A-009, REQ-SYS-004, REQ-SYS-005
  - Archivos: `services/service-a/tests/unit/test_config.py`, `services/service-a/tests/unit/test_logging.py`, `services/service-a/tests/unit/test_health.py`, `services/service-a/tests/integration/test_health_db.py`, `services/service-a/tests/conftest.py`, `services/service-a/tests/integration/conftest.py`
  - Hecho cuando: pruebas escritas en rojo con `@pytest.mark.xfail(strict=True, reason="TASK-A-03")`, referencian sus REQ; `make verify` verde.

- [ ] **TASK-A-03** — Implementación: config, logging JSON, request-id, health, conexión BD
  - Tipo: impl
  - Depende de: TASK-A-02
  - REQ: REQ-A-008, REQ-A-009, REQ-SYS-004, REQ-SYS-005
  - Archivos: `services/service-a/src/books/main.py`, `services/service-a/src/books/config.py`, `services/service-a/src/books/logging.py`, `services/service-a/src/books/api/__init__.py`, `services/service-a/src/books/api/health.py`, `services/service-a/src/books/repository/__init__.py`, `services/service-a/src/books/repository/db.py`, `services/service-a/tests/unit/test_config.py`, `services/service-a/tests/unit/test_logging.py`, `services/service-a/tests/unit/test_health.py`, `services/service-a/tests/integration/test_health_db.py`
  - Hecho cuando: las pruebas de TASK-A-02 pasan; `make verify` verde.

- [ ] **TASK-A-04** — Pruebas: migraciones y repositorio (integración)
  - Tipo: test
  - Depende de: TASK-A-03
  - REQ: REQ-A-012, REQ-A-006, REQ-A-001, REQ-A-002, REQ-A-003, REQ-A-004, REQ-A-005
  - Archivos: `services/service-a/tests/integration/test_migrations.py`, `services/service-a/tests/integration/test_sql_book_repository.py`, `services/service-a/tests/integration/conftest.py`
  - Hecho cuando: pruebas contra PostgreSQL de Testcontainers escritas en rojo (xfail estricto).

- [ ] **TASK-A-05** — Implementación: modelo, migración 0001 y repositorio SQL
  - Tipo: impl
  - Depende de: TASK-A-04
  - REQ: REQ-A-012, REQ-A-006, REQ-A-001, REQ-A-002, REQ-A-003, REQ-A-004, REQ-A-005
  - Archivos: `services/service-a/alembic.ini`, `services/service-a/src/books/repository/models.py`, `services/service-a/src/books/repository/sql_book_repository.py`, `services/service-a/src/books/repository/migrations/**`, `services/service-a/src/books/domain/ports.py`, `services/service-a/src/books/domain/__init__.py`, `services/service-a/tests/integration/test_migrations.py`, `services/service-a/tests/integration/test_sql_book_repository.py`
  - Hecho cuando: se retiran los `xfail`; pruebas de TASK-A-04 pasan (upgrade y downgrade); `make verify` verde.

- [ ] **TASK-A-06** [P] — Pruebas: dominio (ISBN-13, reglas de libro) y capas
  - Tipo: test
  - Depende de: TASK-A-01
  - REQ: REQ-A-007, REQ-A-001
  - Archivos: `services/service-a/tests/unit/test_isbn.py`, `services/service-a/tests/unit/test_book_domain.py`, `services/service-a/tests/unit/test_layers.py`
  - Hecho cuando: pruebas escritas en rojo (xfail estricto); incluyen casos de normalización y dígito de control.

- [ ] **TASK-A-07** — Implementación: dominio
  - Tipo: impl
  - Depende de: TASK-A-06
  - REQ: REQ-A-007, REQ-A-001
  - Archivos: `services/service-a/src/books/domain/isbn.py`, `services/service-a/src/books/domain/book.py`, `services/service-a/src/books/domain/errors.py`, `services/service-a/src/books/domain/__init__.py`, `services/service-a/tests/unit/test_isbn.py`, `services/service-a/tests/unit/test_book_domain.py`, `services/service-a/tests/unit/test_layers.py`
  - Hecho cuando: se retiran los `xfail`; pruebas de TASK-A-06 pasan; el dominio no importa FastAPI/SQLAlchemy; `make verify` verde.

- [ ] **TASK-A-08** — Pruebas: API CRUD con repositorio en memoria
  - Tipo: test
  - Depende de: TASK-A-05, TASK-A-07
  - REQ: REQ-A-001, REQ-A-002, REQ-A-003, REQ-A-004, REQ-A-005, REQ-A-006, REQ-A-007, REQ-SYS-006
  - Archivos: `services/service-a/tests/unit/test_books_api.py`, `services/service-a/tests/unit/fakes.py`, `services/service-a/tests/unit/test_errors.py`
  - Hecho cuando: pruebas escritas en rojo (xfail estricto); cubren todos los escenarios Dado/Cuando/Entonces de REQ-A-001…007.

- [ ] **TASK-A-09** — Implementación: casos de uso y API CRUD + problem+json
  - Tipo: impl
  - Depende de: TASK-A-08
  - REQ: REQ-A-001, REQ-A-002, REQ-A-003, REQ-A-004, REQ-A-005, REQ-A-006, REQ-A-007, REQ-SYS-006
  - Archivos: `services/service-a/src/books/domain/service.py`, `services/service-a/src/books/api/books.py`, `services/service-a/src/books/api/schemas.py`, `services/service-a/src/books/api/errors.py`, `services/service-a/src/books/main.py`, `services/service-a/tests/unit/test_books_api.py`, `services/service-a/tests/unit/test_errors.py`
  - Hecho cuando: se retiran los `xfail`; pruebas de TASK-A-08 pasan; cobertura ≥ 80 %; `make verify` verde.

- [ ] **TASK-A-10** — Pruebas de contrato (schemathesis)
  - Tipo: test
  - Depende de: TASK-A-09
  - REQ: REQ-A-001, REQ-A-002, REQ-A-003, REQ-A-004, REQ-A-005, REQ-A-008, REQ-A-009
  - Archivos: `services/service-a/tests/contract/test_openapi_contract.py`, `services/service-a/tests/contract/conftest.py`
  - Hecho cuando: schemathesis recorre todas las operaciones del contrato sin fallos de conformidad de esquema/estado; `make verify` verde.

- [ ] **TASK-A-11** — Pruebas: búsqueda, filtro y orden
  - Tipo: test
  - Depende de: TASK-A-09
  - REQ: REQ-A-010, REQ-A-011
  - Archivos: `services/service-a/tests/unit/test_books_search.py`, `services/service-a/tests/integration/test_search_sql.py`
  - Hecho cuando: pruebas escritas en rojo (xfail estricto) (incluye acentos: "garcia" encuentra "García").

- [ ] **TASK-A-12** — Implementación: búsqueda, filtro y orden
  - Tipo: impl
  - Depende de: TASK-A-11
  - REQ: REQ-A-010, REQ-A-011
  - Archivos: `services/service-a/src/books/domain/service.py`, `services/service-a/src/books/domain/ports.py`, `services/service-a/src/books/api/books.py`, `services/service-a/src/books/repository/sql_book_repository.py`, `services/service-a/src/books/repository/migrations/**`, `services/service-a/tests/unit/test_books_search.py`, `services/service-a/tests/integration/test_search_sql.py`
  - Hecho cuando: se retiran los `xfail`; pruebas de TASK-A-11 y contrato pasan; `make verify` verde.
