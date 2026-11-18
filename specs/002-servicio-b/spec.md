# 002 · Servicio B — Socios y préstamos

- **Estado**: Borrador para revisión · **Versión**: 0.1.0 · **Fecha**: 2026-11-17
- **Stack**: Node.js · TypeScript · Express · MongoDB 7 · **Contrato**: [contracts/openapi.yaml](contracts/openapi.yaml)
- **Modelo de datos**: [data-model.md](data-model.md) · **Plan**: [plan.md](plan.md) · **Tareas**: [tasks.md](tasks.md)

## Propósito
Gestionar los **socios** de la biblioteca (entidad principal) y sus **préstamos**. Un préstamo
referencia un libro por `book_id` **opaco**: B no consulta ni valida el servicio A (constitución I.3).

## Historias de usuario
- **HU-B-01 (P1)** — Como bibliotecario quiero inscribir, consultar, editar y dar de baja socios.
- **HU-B-02 (P1)** — Como bibliotecario quiero registrar un préstamo de un libro a un socio activo con fecha de devolución.
- **HU-B-03 (P1)** — Como bibliotecario quiero registrar la devolución de un préstamo.
- **HU-B-04 (P1)** — Como bibliotecario quiero listar préstamos por socio, por libro o por estado.
- **HU-B-05 (P2)** — Como bibliotecario quiero ver qué préstamos están vencidos.
- **HU-B-06 (P2)** — Como bibliotecario quiero suspender a un socio para impedir nuevos préstamos.
- **HU-B-07 (P1)** — Como operador quiero endpoints de salud e índices creados automáticamente.

## Requisitos funcionales — socios

### REQ-B-001 — Crear socio (P1)
`POST /members` con `full_name`, `email` (obligatorios), `phone` (opcional). `status` inicial `active`.
El email se normaliza (recorte + minúsculas). Responde `201` + `Location: /members/{id}`.
- **Dado** un cuerpo válido, **cuando** creo el socio, **entonces** `201` con `status: "active"` y `email` en minúsculas.

### REQ-B-002 — Obtener socio (P1)
`GET /members/{id}` → `200`; inexistente → `404`; id no-UUID → `422`.
- **Dado** un socio existente, **cuando** pido su id, **entonces** `200` con el socio y `active_loans` (número de préstamos no devueltos).

### REQ-B-003 — Listar socios (P1)
`GET /members?limit&offset&status&q` paginado `{items,total,limit,offset}` (limit 20 por defecto, máx. 100).
`status` ∈ {`active`,`suspended`}; `q` busca subcadena en `full_name` o `email` sin distinguir mayúsculas.
Orden: `created_at` desc, desempate `id`.
- **Dado** 3 socios activos y 1 suspendido, **cuando** pido `status=suspended`, **entonces** 1 item y `total=1`.

### REQ-B-004 — Actualizar socio (P1)
`PUT /members/{id}` reemplaza `full_name`, `email`, `phone`, `status`. Actualiza `updated_at`.
- **Dado** un socio, **cuando** lo actualizo con `status: "suspended"`, **entonces** `200` y ya no puede tomar préstamos (REQ-B-008).

### REQ-B-005 — Eliminar socio (P1)
`DELETE /members/{id}` → `204`. Si tiene préstamos activos (no devueltos) → `409 /problems/member-has-active-loans`.
Al eliminar, sus préstamos ya devueltos también se eliminan.
- **Dado** un socio con un préstamo activo, **cuando** lo elimino, **entonces** `409` y sigue existiendo.
- **Dado** un socio sin préstamos activos, **cuando** lo elimino, **entonces** `204` y `GET` da `404`.

### REQ-B-006 — Email único (P1)
- **Dado** un socio con `ana@example.com`, **cuando** creo o actualizo otro con `ANA@example.com`, **entonces** `409 /problems/duplicate-email`.

### REQ-B-007 — Validación de entrada (P1)
`full_name` 1–120 caracteres tras recortar; `email` formato válido ≤ 254; `phone` opcional, `^\+?[0-9 ()-]{7,20}$`;
`status` enum; campos desconocidos → rechazo. Errores → `422` problem+json con `errors[]`.
- **Dado** `email: "no-es-email"`, **entonces** `422` con `errors[].field = "body.email"`.

## Requisitos funcionales — préstamos

### REQ-B-008 — Crear préstamo (P1)
`POST /loans` con `member_id`, `book_id` (UUID, opaco), `due_date` opcional (`YYYY-MM-DD`).
Reglas:
1. El socio debe existir → si no, `422 /problems/member-not-found`.
2. El socio debe estar `active` → si no, `409 /problems/member-not-eligible`.
3. El socio no puede superar `SERVICE_B_MAX_ACTIVE_LOANS` préstamos activos (default **3**) → `409 /problems/loan-limit-reached`.
4. `due_date` por defecto = hoy (UTC) + `SERVICE_B_DEFAULT_LOAN_DAYS` (default **14**); si se envía, debe ser > hoy y ≤ hoy + 90 días → si no, `422`.
5. El mismo socio no puede tener dos préstamos activos del mismo `book_id` → `409 /problems/duplicate-active-loan`.
Responde `201` + `Location: /loans/{id}` con `status: "active"`, `loaned_at`, `due_date`, `returned_at: null`.
- **Dado** un socio activo con 0 préstamos, **cuando** presto un libro sin `due_date`, **entonces** `201` y `due_date` = hoy + 14.
- **Dado** un socio con 3 préstamos activos, **cuando** pido otro, **entonces** `409 loan-limit-reached`.
- **Dado** un socio suspendido, **entonces** `409 member-not-eligible`.

### REQ-B-009 — Listar préstamos (P1)
`GET /loans?member_id&book_id&status&limit&offset` paginado; `status` ∈ {`active`,`returned`,`overdue`}.
Orden `loaned_at` desc.
- **Dado** préstamos de dos socios, **cuando** filtro por `member_id`, **entonces** solo los de ese socio.

### REQ-B-010 — Obtener préstamo (P1)
`GET /loans/{id}` → `200`; inexistente → `404`.

### REQ-B-011 — Devolver préstamo (P1)
`POST /loans/{id}/return` fija `returned_at = ahora` y `status = returned` → `200`.
- **Dado** un préstamo activo, **cuando** lo devuelvo, **entonces** `200` con `returned_at` no nulo.
- **Dado** un préstamo ya devuelto, **cuando** lo devuelvo otra vez, **entonces** `409 /problems/loan-already-returned`.

### REQ-B-012 — Estado vencido derivado (P2)
`status` se calcula al leer: `returned` si `returned_at` ≠ null; si no, `overdue` si `due_date` < hoy (UTC); si no, `active`.
Un préstamo vencido cuenta como activo para REQ-B-005 y REQ-B-008.
- **Dado** un préstamo con `due_date` de ayer sin devolver, **cuando** lo consulto, **entonces** `status: "overdue"`.
- **Dado** `status=overdue` en el listado, **entonces** solo préstamos vencidos no devueltos.

## Requisitos funcionales — operación

### REQ-B-013 — Liveness (P1)
`GET /health/live` → `200 {"status":"ok"}` sin consultar MongoDB.

### REQ-B-014 — Readiness (P1)
`GET /health/ready` ejecuta `ping` a MongoDB con timeout ≤ 2 s → `200` / `503` (mismo formato que A).

### REQ-B-015 — Índices al arranque (P1)
Al iniciar, B crea (idempotente) los índices definidos en [data-model.md](data-model.md) antes de aceptar tráfico.
- **Dado** una BD vacía, **cuando** arranca B, **entonces** existe el índice único `uq_members_email`.

## Requisitos no funcionales
| ID | Requisito | Verificado por |
|---|---|---|
| NFR-B-001 | Cobertura de líneas ≥ 80 % | umbral de vitest en `make verify` |
| NFR-B-002 | `tsc --strict --noEmit` y ESLint sin errores | `make verify` |
| NFR-B-003 | Logs JSON (REQ-SYS-004) y config por entorno (REQ-SYS-005) | tests de B-02 |
| NFR-B-004 | Imagen no-root < 250 MB | `tests/platform` |
| NFR-B-005 | Fechas en UTC; `due_date` como fecha sin hora | tests de dominio |

## Fuera de alcance
- Validar que `book_id` exista en A, o disponibilidad/copias del libro.
- Renovaciones, reservas, multas y cobros, notificaciones de vencimiento.
- Edición o borrado de préstamos (salvo la devolución y el borrado en cascada de REQ-B-005).
- Historial de cambios de socios, carnés, fotos, direcciones.
- Autenticación de socios (el único actor es el bibliotecario).
- Transacciones multi-documento / replica set de MongoDB.

## Preguntas abiertas
- [NEEDS CLARIFICATION] **Q-B-1**: límite de préstamos activos por socio — se asumió **3** (configurable). ¿Correcto?
- [NEEDS CLARIFICATION] **Q-B-2**: plazo de préstamo — se asumió **14 días** por defecto y máximo 90. ¿Correcto?
- [NEEDS CLARIFICATION] **Q-B-3**: ¿un mismo `book_id` puede estar prestado a varios socios a la vez? Hoy **sí** (A no tiene copias); solo se impide que el mismo socio lo duplique.
- [NEEDS CLARIFICATION] **Q-B-4**: al borrar un socio, ¿se borran sus préstamos devueltos (hoy sí) o se conservan como histórico?
- [NEEDS CLARIFICATION] **Q-B-5**: Node.js 20 llegó a fin de vida en abril de 2026. ¿Mantener Node 20 por requisito o usar Node 22/24 LTS? (El plan asume **Node 22 LTS** hasta confirmación.)
- [NEEDS CLARIFICATION] **Q-B-6**: sin replica set no hay transacciones; la regla "máx. N préstamos activos" puede violarse con peticiones concurrentes. ¿Se acepta esa carrera en alcance académico?
