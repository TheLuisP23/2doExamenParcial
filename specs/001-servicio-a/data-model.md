# 001 · Servicio A — modelo de datos (PostgreSQL 16)

Base de datos `books`, esquema `public`, propiedad del usuario `books` (exclusivo de A).
Gestionado con **Alembic**; ninguna otra aplicación accede a esta BD.

## Tabla `books`
| Columna | Tipo | Nulo | Default | Restricciones |
|---|---|---|---|---|
| `id` | `uuid` | no | `gen_random_uuid()` | PK |
| `isbn` | `varchar(13)` | no | — | `UNIQUE` (`uq_books_isbn`), `CHECK (isbn ~ '^97[89][0-9]{10}$')` |
| `title` | `varchar(255)` | no | — | `CHECK (length(btrim(title)) > 0)` |
| `author` | `varchar(255)` | no | — | `CHECK (length(btrim(author)) > 0)` |
| `publisher` | `varchar(255)` | sí | `NULL` | — |
| `published_year` | `smallint` | sí | `NULL` | `CHECK (published_year BETWEEN 1450 AND 2100)` (el límite "≤ año actual" lo aplica el dominio) |
| `genre` | `varchar(64)` | sí | `NULL` | — |
| `created_at` | `timestamptz` | no | `now()` | — |
| `updated_at` | `timestamptz` | no | `now()` | actualizado por la aplicación en cada `PUT` |

El dígito de control del ISBN se valida en el **dominio**; la BD solo garantiza forma y unicidad.

## Índices
| Nombre | Definición | Uso |
|---|---|---|
| `uq_books_isbn` | `UNIQUE (isbn)` | REQ-A-006 |
| `ix_books_created_at_id` | `(created_at DESC, id)` | orden por defecto y paginación estable (REQ-A-003) |
| `ix_books_title_trgm` | `GIN (immutable_unaccent(lower(title)) gin_trgm_ops)` | búsqueda `q` (REQ-A-010) |
| `ix_books_author_trgm` | `GIN (immutable_unaccent(lower(author)) gin_trgm_ops)` | búsqueda `q` (REQ-A-010) |
| `ix_books_genre_lower` | `(lower(genre))` | filtro `genre` (REQ-A-010) |

Extensiones requeridas (creadas por la migración inicial): `pg_trgm`, `unaccent`. Se define la
función `immutable_unaccent(text)` (wrapper `IMMUTABLE` de `unaccent`) para poder indexarla.

## Migraciones
- `0001_create_books` — extensiones, función, tabla e índices.
- Convención: un archivo por cambio, `upgrade()` y `downgrade()` obligatorios, probados en integración.

## Mapeo dominio ↔ persistencia ↔ API
| Dominio (`Book`) | Columna | JSON (contrato) |
|---|---|---|
| `id: UUID` | `id` | `id` (string, uuid) |
| `isbn: Isbn13` | `isbn` | `isbn` |
| `title: str` | `title` | `title` |
| `author: str` | `author` | `author` |
| `publisher: str \| None` | `publisher` | `publisher` (nullable) |
| `published_year: int \| None` | `published_year` | `published_year` (nullable) |
| `genre: str \| None` | `genre` | `genre` (nullable) |
| `created_at: datetime` | `created_at` | `created_at` (date-time, UTC) |
| `updated_at: datetime` | `updated_at` | `updated_at` (date-time, UTC) |

## Datos de ejemplo (seed de desarrollo, opcional)
```json
{"isbn": "9780307474728", "title": "Cien años de soledad", "author": "Gabriel García Márquez", "published_year": 1967, "genre": "novela"}
```
