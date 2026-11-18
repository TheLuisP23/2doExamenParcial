# 002 · Servicio B — modelo de datos (MongoDB 7)

Base de datos `members` (exclusiva de B), usuario de aplicación con rol `readWrite` solo sobre ella.
Despliegue standalone (sin replica set → sin transacciones multi-documento; ver Q-B-6).
Los `_id` son **UUID v4 en string** (no ObjectId) para un formato de id uniforme en la API.

## Colección `members`
```json
{
  "_id": "6f1c2b9e-8a7d-4c1e-9b0a-1d2e3f4a5b6c",
  "full_name": "Ana Pérez",
  "email": "ana@example.com",
  "phone": "+57 300 123 4567",
  "status": "active",
  "created_at": {"$date": "2026-11-17T10:00:00Z"},
  "updated_at": {"$date": "2026-11-17T10:00:00Z"}
}
```
| Campo | Tipo BSON | Obligatorio | Reglas |
|---|---|---|---|
| `_id` | string (UUID) | sí | generado por B |
| `full_name` | string | sí | 1–120 tras recortar |
| `email` | string | sí | minúsculas, único |
| `phone` | string \| null | no | `^\+?[0-9 ()-]{7,20}$` |
| `status` | string | sí | `active` \| `suspended` |
| `created_at`, `updated_at` | date | sí | UTC |

Validador `$jsonSchema` de colección (nivel `strict`, acción `error`) con las mismas reglas de tipo/enum.

## Colección `loans`
```json
{
  "_id": "0b8f8a6e-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
  "member_id": "6f1c2b9e-8a7d-4c1e-9b0a-1d2e3f4a5b6c",
  "book_id": "3f1c2b9e-8a7d-4c1e-9b0a-1d2e3f4a5b6c",
  "loaned_at": {"$date": "2026-11-17T10:05:00Z"},
  "due_date": "2026-12-01",
  "returned_at": null
}
```
| Campo | Tipo BSON | Obligatorio | Reglas |
|---|---|---|---|
| `_id` | string (UUID) | sí | generado por B |
| `member_id` | string (UUID) | sí | referencia a `members._id` (misma BD) |
| `book_id` | string (UUID) | sí | **opaco**, id de A; nunca se valida contra A |
| `loaned_at` | date | sí | UTC, momento de creación |
| `due_date` | string `YYYY-MM-DD` | sí | fecha sin hora (comparación lexicográfica = cronológica) |
| `returned_at` | date \| null | sí | `null` mientras está activo |

`status` **no se persiste**; se deriva (REQ-B-012):
`returned_at != null → returned`; `due_date < hoy → overdue`; si no `active`.
Filtros por estado en consultas: `active` → `{returned_at: null, due_date: {$gte: hoy}}`;
`overdue` → `{returned_at: null, due_date: {$lt: hoy}}`; `returned` → `{returned_at: {$ne: null}}`.

## Índices (creados al arranque, REQ-B-015)
| Colección | Nombre | Clave | Opciones | Uso |
|---|---|---|---|---|
| members | `uq_members_email` | `{email: 1}` | `unique` | REQ-B-006 |
| members | `ix_members_status_created` | `{status: 1, created_at: -1, _id: 1}` | — | REQ-B-003 |
| loans | `ix_loans_member_open` | `{member_id: 1, returned_at: 1}` | — | REQ-B-005, REQ-B-008 (conteo activos) |
| loans | `uq_loans_member_book_open` | `{member_id: 1, book_id: 1}` | `unique`, `partialFilterExpression: {returned_at: null}` | REQ-B-008 regla 5 |
| loans | `ix_loans_book` | `{book_id: 1, loaned_at: -1}` | — | REQ-B-009 |
| loans | `ix_loans_loaned_at` | `{loaned_at: -1}` | — | orden por defecto |

> Nota: `partialFilterExpression` no admite `{returned_at: null}` con `$eq: null` en todas las
> versiones; si MongoDB 7 lo rechaza se usa `{returned_at: {$type: "null"}}`. Verificado en TASK-B-04.

## Mapeo API ↔ documento
API usa `id` (= `_id`), fechas RFC 3339 y `due_date` como `date`. `active_loans` en `Member` se calcula
con `countDocuments({member_id, returned_at: null})` (no se persiste).
