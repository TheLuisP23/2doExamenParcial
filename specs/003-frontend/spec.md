# 003 · Frontend — SPA del bibliotecario

- **Estado**: Borrador para revisión · **Versión**: 0.1.0 · **Fecha**: 2026-11-17
- **Stack**: React · Vite · TypeScript · Nginx · **Consume**: [contrato A](../001-servicio-a/contracts/openapi.yaml), [contrato B](../002-servicio-b/contracts/openapi.yaml)
- **Plan**: [plan.md](plan.md) · **Tareas**: [tasks.md](tasks.md)

## Propósito
Interfaz web única para el bibliotecario. Es el **único** lugar donde se combinan datos de A y B
(p. ej. el préstamo muestra el título del libro). Nginx sirve la SPA y hace de proxy reverso.

## Mapa de pantallas
| Ruta | Pantalla | REQ |
|---|---|---|
| `/` | redirige a `/libros` | — |
| `/libros` · `/libros/nuevo` · `/libros/:id/editar` | catálogo, alta, edición | F-001, F-002, F-003 |
| `/socios` · `/socios/nuevo` · `/socios/:id/editar` | socios | F-004 |
| `/prestamos` · `/prestamos/nuevo` | préstamos | F-005, F-006 |

## Historias de usuario
- **HU-F-01 (P1)** — Como bibliotecario quiero navegar y buscar en el catálogo.
- **HU-F-02 (P1)** — Como bibliotecario quiero dar de alta, editar y borrar libros desde formularios con validación inmediata.
- **HU-F-03 (P1)** — Como bibliotecario quiero gestionar socios (alta, edición, suspensión, baja).
- **HU-F-04 (P1)** — Como bibliotecario quiero prestar un libro a un socio eligiéndolos de listas, y registrar devoluciones.
- **HU-F-05 (P1)** — Como bibliotecario quiero mensajes de error comprensibles cuando algo falla.
- **HU-F-06 (P3)** — Como bibliotecario que usa teclado/lector de pantalla quiero una interfaz accesible.

## Requisitos funcionales

### REQ-F-001 — Catálogo paginado con búsqueda (P1)
`/libros` lista libros (título, autor, año, ISBN) usando `GET /api/a/books`, con paginación
(anterior/siguiente, 20 por página) y un buscador que envía `q` con *debounce* de 300 ms.
- **Dado** 25 libros, **cuando** abro `/libros`, **entonces** veo 20 y el control "Siguiente" habilitado.
- **Dado** que escribo "borges", **cuando** pasan 300 ms, **entonces** se pide `q=borges` y solo veo coincidencias.
- **Dado** que no hay resultados, **entonces** veo el estado vacío "No hay libros".

### REQ-F-002 — Alta y edición de libro (P1)
Formulario con los campos de `BookInput`; validación en cliente equivalente al contrato
(obligatorios, longitudes, ISBN-13 con dígito de control, año ≤ actual). Envía `POST` o `PUT`.
- **Dado** un ISBN con dígito de control incorrecto, **cuando** salgo del campo, **entonces** veo el error bajo el campo y "Guardar" no envía.
- **Dado** un `409 duplicate-isbn` del servidor, **entonces** el error aparece en el campo ISBN.
- **Dado** un guardado correcto, **entonces** vuelvo a `/libros` con un aviso "Libro guardado".

### REQ-F-003 — Baja de libro con confirmación (P1)
- **Dado** un libro, **cuando** pulso "Eliminar", **entonces** se pide confirmación y solo tras confirmar se envía `DELETE`; la lista se actualiza.

### REQ-F-004 — Gestión de socios (P1)
`/socios`: listado paginado con filtro por estado y búsqueda; alta, edición (incluido cambiar
estado a suspendido) y baja con confirmación. Muestra `active_loans`.
- **Dado** un socio con préstamos activos, **cuando** intento eliminarlo, **entonces** veo el mensaje del `409 member-has-active-loans` y el socio sigue en la lista.

### REQ-F-005 — Nuevo préstamo componiendo A y B (P1)
`/prestamos/nuevo`: selector de **socio activo** (búsqueda en `GET /api/b/members?status=active&q=`)
y selector de **libro** (búsqueda en `GET /api/a/books?q=`); fecha de devolución opcional. Envía
`POST /api/b/loans` con `member_id` y `book_id`.
- **Dado** que elijo socio y libro, **cuando** confirmo, **entonces** se crea el préstamo y voy a `/prestamos`.
- **Dado** un `409 loan-limit-reached`, **entonces** veo "El socio alcanzó el máximo de préstamos activos".

### REQ-F-006 — Listado y devolución de préstamos (P1)
`/prestamos` lista préstamos con filtro por estado (`active`/`overdue`/`returned`) y por socio.
Cada fila muestra el nombre del socio (de B) y el **título del libro resuelto desde A**
(`GET /api/a/books/{id}`, cacheado). Si A responde 404, muestra "Libro no disponible".
Botón "Registrar devolución" en préstamos no devueltos. Los vencidos se destacan visualmente.
- **Dado** un préstamo activo, **cuando** pulso "Registrar devolución", **entonces** cambia a "Devuelto" sin recargar la página.
- **Dado** un préstamo cuyo libro fue borrado en A, **entonces** veo "Libro no disponible" y el resto de la fila.
- **Dado** que A no responde, **entonces** la lista de préstamos se muestra igual con el título como "—" (degradación elegante).

### REQ-F-007 — Manejo de errores (P1)
Respuestas `application/problem+json`: se muestra `detail` (o un texto por `type` conocido);
`errors[]` de validación se asignan a sus campos; errores de red/5xx muestran un banner
"Servicio no disponible, reintenta" con botón de reintento.
- **Dado** que B devuelve `503`, **cuando** abro `/socios`, **entonces** veo el banner y el botón "Reintentar".

### REQ-F-008 — Nginx: SPA, proxy y salud (P1)
- Sirve `index.html` para cualquier ruta que no sea un archivo ni `/api/*` (fallback de SPA).
- `location /api/a/` → `proxy_pass $SERVICE_A_UPSTREAM/` (quita el prefijo); ídem `/api/b/`.
- Añade/propaga `X-Request-ID`; no añade cabeceras CORS.
- `GET /health/live` y `/health/ready` responden `200 {"status":"ok"}` desde el propio Nginx.
- Assets con hash: `Cache-Control: public, max-age=31536000, immutable`; `index.html`: `no-cache`.
- Cabeceras: `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`.
- **Dado** `GET /socios/123/editar`, **entonces** `200` con `index.html`.
- **Dado** `GET /api/a/books`, **entonces** el upstream A recibe `GET /books`.

### REQ-F-009 — Configuración sin hosts embebidos (P1)
El bundle usa solo rutas relativas `/api/a` y `/api/b` (sin `VITE_*` con hosts). Los upstreams
de Nginx vienen de variables de entorno `SERVICE_A_UPSTREAM`, `SERVICE_B_UPSTREAM` (plantillas `envsubst`).
- **Dado** el bundle de producción, **cuando** se busca `http://` en `dist/assets/*.js`, **entonces** no hay hosts de servicios.

### REQ-F-010 — Accesibilidad básica (P3)
Etiquetas en todos los campos, foco visible, navegación por teclado y sin violaciones axe `serious`/`critical`.
- **Dado** cada pantalla principal, **cuando** se analiza con axe, **entonces** 0 violaciones serias o críticas.

## Requisitos no funcionales
| ID | Requisito | Verificado por |
|---|---|---|
| NFR-F-001 | Cobertura ≥ 80 % (vitest) | `make verify` |
| NFR-F-002 | `tsc --noEmit` y ESLint sin errores | `make verify` |
| NFR-F-003 | Bundle JS inicial < 300 kB gzip | chequeo de tamaño en build (P3) |
| NFR-F-004 | Navegadores: últimas 2 versiones de Chrome/Firefox/Edge | Playwright (chromium + firefox) |
| NFR-F-005 | Tipos de API generados de los `openapi.yaml` (no escritos a mano) | `npm run gen:api` + diff en verify |

## Fuera de alcance
- Login, sesiones, roles; modo oscuro; i18n (solo español); PWA/offline.
- Diseño visual elaborado / librería de componentes de terceros.
- SSR; despliegue en CDN/S3.
- Lógica de negocio de préstamos en el cliente (las reglas las aplica B; el front solo muestra sus errores).

## Preguntas abiertas
- [NEEDS CLARIFICATION] **Q-F-1**: ¿hace falta una pantalla de detalle de socio con su historial de préstamos (P2)? Hoy se usa el filtro por socio en `/prestamos`.
- [NEEDS CLARIFICATION] **Q-F-2**: ¿alguna guía visual/identidad institucional que seguir?
