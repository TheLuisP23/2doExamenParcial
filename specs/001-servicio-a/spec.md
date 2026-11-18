# 001 · Servicio A — Catálogo de libros

- **Estado**: Borrador para revisión · **Versión**: 0.1.0 · **Fecha**: 2026-11-17
- **Stack**: Python 3.12 · FastAPI · PostgreSQL 16 · **Contrato**: [contracts/openapi.yaml](contracts/openapi.yaml)
- **Modelo de datos**: [data-model.md](data-model.md) · **Plan**: [plan.md](plan.md) · **Tareas**: [tasks.md](tasks.md)

## Propósito
Mantener el catálogo de libros de la biblioteca (alta, consulta, edición, baja y búsqueda).
Es la única fuente de verdad de los libros. No sabe nada de socios ni préstamos.

## Historias de usuario
- **HU-A-01 (P1)** — Como bibliotecario quiero registrar un libro con su ISBN, título y autor para tenerlo en el catálogo.
- **HU-A-02 (P1)** — Como bibliotecario quiero ver el detalle de un libro y la lista paginada del catálogo.
- **HU-A-03 (P1)** — Como bibliotecario quiero corregir los datos de un libro o darlo de baja.
- **HU-A-04 (P2)** — Como bibliotecario quiero buscar libros por título o autor y filtrar por género.
- **HU-A-05 (P3)** — Como bibliotecario quiero ordenar el listado por título, autor o fecha de alta.
- **HU-A-06 (P1)** — Como operador quiero endpoints de salud y migraciones automáticas para desplegar sin pasos manuales.

## Requisitos funcionales

### REQ-A-001 — Crear libro (P1)
`POST /books` con `isbn`, `title`, `author` (obligatorios) y `publisher`, `published_year`, `genre`
(opcionales). Devuelve `201`, cabecera `Location: /books/{id}` y el libro con `id`, `created_at`, `updated_at`.
El ISBN se normaliza quitando guiones y espacios antes de validar y guardar.
- **Dado** un cuerpo válido, **cuando** hago `POST /books`, **entonces** `201`, `Location` y el cuerpo cumple `Book`.
- **Dado** `isbn: "978-0-306-40615-7"`, **cuando** creo el libro, **entonces** se guarda y devuelve `"9780306406157"`.

### REQ-A-002 — Obtener libro (P1)
`GET /books/{id}` devuelve el libro.
- **Dado** un libro existente, **cuando** pido su id, **entonces** `200` con el libro.
- **Dado** un UUID inexistente, **entonces** `404` problem+json.
- **Dado** un id que no es UUID, **entonces** `422` problem+json.

### REQ-A-003 — Listar libros paginado (P1)
`GET /books?limit&offset` devuelve `{items, total, limit, offset}`. `limit` por defecto 20, máx. 100;
`offset` por defecto 0. Orden por defecto: `created_at` descendente, desempate por `id`.
- **Dado** 25 libros, **cuando** pido `limit=10&offset=20`, **entonces** 5 items y `total=25`.
- **Dado** `limit=101` o `offset=-1`, **entonces** `422`.

### REQ-A-004 — Actualizar libro (P1)
`PUT /books/{id}` reemplaza todos los campos editables (mismo esquema que la creación) y actualiza `updated_at`.
- **Dado** un libro existente y cuerpo válido, **cuando** hago `PUT`, **entonces** `200` con los nuevos valores y `updated_at` > anterior.
- **Dado** un id inexistente, **entonces** `404`.

### REQ-A-005 — Eliminar libro (P1)
`DELETE /books/{id}` elimina definitivamente (borrado físico).
- **Dado** un libro existente, **cuando** lo elimino, **entonces** `204` y un `GET` posterior da `404`.
- **Dado** un id inexistente, **entonces** `404`.

### REQ-A-006 — ISBN único (P1)
No puede haber dos libros con el mismo ISBN normalizado.
- **Dado** un libro con ISBN X, **cuando** creo o actualizo otro con ISBN X, **entonces** `409` problem+json con `type: /problems/duplicate-isbn`.

### REQ-A-007 — Validación de entrada (P1)
Reglas: `isbn` ISBN-13 con dígito de control válido (prefijo 978/979); `title` y `author` 1–255
caracteres tras recortar espacios; `publisher` ≤ 255; `published_year` entero entre 1450 y el año
actual; `genre` ≤ 64; campos desconocidos rechazados.
- **Dado** un ISBN con dígito de control incorrecto, **entonces** `422` con `errors[]` que señala `isbn`.
- **Dado** `published_year` futuro, **entonces** `422`.
- **Dado** un campo extra `foo`, **entonces** `422`.

### REQ-A-008 — Liveness (P1)
`GET /health/live` → `200 {"status":"ok"}` sin consultar la BD.
- **Dado** el proceso en marcha y la BD caída, **cuando** pido `/health/live`, **entonces** `200`.

### REQ-A-009 — Readiness (P1)
`GET /health/ready` ejecuta `SELECT 1` con timeout ≤ 2 s.
- **Dado** la BD disponible, **entonces** `200 {"status":"ok","checks":{"database":"ok"}}`.
- **Dado** la BD caída, **entonces** `503 {"status":"unavailable","checks":{"database":"error"}}`.

### REQ-A-010 — Búsqueda y filtro (P2)
`GET /books?q=texto&genre=g`: `q` busca subcadena sin distinguir mayúsculas/acentos en `title` o
`author`; `genre` es coincidencia exacta sin distinguir mayúsculas. Combinables con paginación.
- **Dado** libros de "García Márquez" y "Borges", **cuando** pido `q=garcia`, **entonces** solo los del primero.

### REQ-A-011 — Ordenamiento (P3)
`sort` ∈ {`title`, `-title`, `author`, `-author`, `created_at`, `-created_at`} (por defecto `-created_at`).
- **Dado** `sort=title`, **entonces** items en orden alfabético ascendente.
- **Dado** `sort=precio`, **entonces** `422`.

### REQ-A-012 — Migraciones versionadas (P1)
El esquema se gestiona con Alembic. Las migraciones se aplican antes de aceptar tráfico
(comando de arranque `migrate && serve`) y son idempotentes.
- **Dado** una BD vacía, **cuando** arranca el servicio, **entonces** la tabla `books` existe con la versión de Alembic más reciente.
- **Dado** una BD ya migrada, **cuando** arranca de nuevo, **entonces** no falla ni duplica nada.

## Requisitos no funcionales
| ID | Requisito | Verificado por |
|---|---|---|
| NFR-A-001 | Cobertura de líneas ≥ 80 % | `pytest --cov-fail-under=80` en `make verify` |
| NFR-A-002 | p95 < 200 ms para `GET /books` con 1 000 libros (local) | prueba de rendimiento manual opcional (P3) |
| NFR-A-003 | Logs JSON (REQ-SYS-004) y config por entorno (REQ-SYS-005) | tests de A-02 |
| NFR-A-004 | Imagen no-root < 200 MB | `tests/platform` |
| NFR-A-005 | Tipado estricto (`mypy --strict`) y `ruff` sin errores | `make verify` |

## Fuera de alcance
- Inventario de ejemplares/copias y disponibilidad (A no sabe de préstamos).
- Portadas/imágenes, reseñas, valoraciones, categorías jerárquicas.
- Importación masiva (CSV) e integración con APIs externas de ISBN.
- Borrado lógico, auditoría e historial de cambios; control de concurrencia optimista (ETag).
- Autenticación/autorización.
- Búsqueda full-text avanzada (relevancia, sinónimos).

## Preguntas abiertas (resueltas 2026-11-17)
- Q-A-1: solo ISBN-13 (ISBN-10 fuera de alcance).
- Q-A-2: `genre` texto libre ≤ 64.
- Q-A-3: sin `total_copies`.
- Q-A-4: se acepta borrar libros con préstamos activos en B; el front muestra "Libro no disponible".
