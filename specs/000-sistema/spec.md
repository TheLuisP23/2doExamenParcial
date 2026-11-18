# 000 · Sistema — especificación transversal

- **Estado**: Borrador para revisión · **Versión**: 0.1.0 · **Fecha**: 2026-11-17
- **Componentes**: servicio A, servicio B, frontend, plataforma
- **Relacionadas**: [001](../001-servicio-a/spec.md) · [002](../002-servicio-b/spec.md) ·
  [003](../003-frontend/spec.md) · [004](../004-plataforma/spec.md) · [constitución](../constitution.md)

## Visión
Una biblioteca pequeña quiere gestionar su **catálogo de libros**, sus **socios** y los
**préstamos**. El catálogo (A) y la gestión de socios/préstamos (B) son servicios autónomos;
el frontend los compone para el usuario (bibliotecario).

## Glosario
| Término | Definición |
|---|---|
| Libro (`Book`) | Título catalogado, identificado por UUID y por ISBN-13 único. Vive en A. |
| Socio (`Member`) | Persona inscrita que puede tomar préstamos. Vive en B. |
| Préstamo (`Loan`) | Registro de que un socio tiene un libro (por `book_id` opaco) hasta una fecha. Vive en B. |
| Bibliotecario | Único actor humano del sistema (usuario del frontend). |
| Origen único | Todo el tráfico del navegador va al mismo host:puerto (Nginx). |

## Actores
- **Bibliotecario** (humano, navegador).
- **Operador de plataforma** (humano, AWS CLI / kubectl).
- **GitHub Actions** (CI/CD, vía OIDC).

## Historias de usuario
- **HU-SYS-01 (P1)** — Como bibliotecario quiero usar una sola URL para todo el sistema para no
  lidiar con varios hosts ni errores de CORS.
- **HU-SYS-02 (P1)** — Como equipo quiero que A y B evolucionen y se desplieguen por separado
  para que el fallo o cambio de uno no rompa al otro.
- **HU-SYS-03 (P1)** — Como operador quiero endpoints de salud uniformes para que Kubernetes y
  los smoke tests sepan si cada componente está vivo y listo.
- **HU-SYS-04 (P2)** — Como operador quiero logs JSON correlacionables por petición para
  diagnosticar problemas.

## Requisitos funcionales y transversales

### REQ-SYS-001 — Origen único con proxy reverso (P1)
El navegador solo habla con Nginx. `/api/a/*` se reenvía al servicio A y `/api/b/*` al servicio B,
**quitando el prefijo** (`/api/a/books` → A recibe `/books`). Cualquier otra ruta sirve la SPA.
No se emiten cabeceras CORS.
- **Dado** el stack levantado, **cuando** el navegador pide `GET /api/a/health/live` al origen del
  front, **entonces** recibe `200` producido por el servicio A.
- **Dado** el stack levantado, **cuando** se pide `GET /api/b/health/live`, **entonces** responde B.
- **Dado** cualquier respuesta de `/api/*`, **entonces** no contiene `Access-Control-Allow-Origin`.

### REQ-SYS-002 — Independencia de servicios (P1)
A y B no comparten BD, código ni librerías y no se invocan entre sí.
- **Dado** el código de `services/service-a`, **cuando** se analiza, **entonces** no importa ni
  referencia rutas de `services/service-b` (y viceversa).
- **Dado** la configuración de A, **entonces** no contiene ninguna variable/URL que apunte a B ni a
  MongoDB; la de B no apunta a A ni a PostgreSQL.
- **Dado** los manifiestos k8s, **entonces** cada BD tiene su propio StatefulSet, Secret y Service.

### REQ-SYS-003 — Endpoints de salud uniformes (P1)
A, B y el front exponen `GET /health/live` y `GET /health/ready`, que devuelven
`200 {"status":"ok"}` o `503 {"status":"unavailable", ...}`. `live` no consulta dependencias.
- **Dado** un componente en marcha, **cuando** se pide `/health/live`, **entonces** `200`.
- **Dado** que la BD del servicio no responde, **cuando** se pide `/health/ready`, **entonces** `503`.

### REQ-SYS-004 — Logs JSON correlacionados (P2)
Nginx genera `X-Request-ID` si no viene y lo propaga; A y B lo incluyen como `request_id` en cada
línea de log JSON y lo devuelven en la cabecera de respuesta.
- **Dado** una petición sin `X-Request-ID`, **cuando** pasa por Nginx, **entonces** la respuesta
  trae `X-Request-ID` y el log del servicio tiene el mismo valor.

### REQ-SYS-005 — Configuración por entorno con fallo rápido (P1)
Toda configuración llega por variables de entorno documentadas en `.env.example`. Si falta una
obligatoria, el proceso termina al arrancar con código ≠ 0 y un log claro.
- **Dado** que falta `SERVICE_A_DATABASE_URL`, **cuando** arranca A, **entonces** sale con error.
- **Dado** que falta `SERVICE_B_MONGO_URI`, **cuando** arranca B, **entonces** sale con error.

### REQ-SYS-006 — Errores problem+json (P1)
A y B responden todo error 4xx/5xx con `Content-Type: application/problem+json` y campos
`type`, `title`, `status`, `detail` (y `errors[]` en validación). **Excepción**: `/health/*` responde
siempre con el esquema `Health` de REQ-SYS-003 (también el `503`), porque lo consumen probes y balanceadores.
- **Dado** un recurso inexistente, **cuando** se pide, **entonces** `404` con cuerpo problem+json.

## Requisitos no funcionales
| ID | Requisito | Verificado por |
|---|---|---|
| NFR-SYS-001 | Cobertura ≥ 80 % por componente | umbral en pytest/vitest dentro de `make verify` |
| NFR-SYS-002 | Imágenes no-root y con base fijada | `tests/platform` + platform-engineer |
| NFR-SYS-003 | Arranque local completo con un comando (`./init.sh --up`) | smoke de `init.sh` |
| NFR-SYS-004 | Sin secretos en repo | gitleaks (pre-commit + CI) |

## Fuera de alcance
- Autenticación/autorización de usuarios finales y roles (el sistema es de uso interno académico).
- Comunicación entre servicios (síncrona o asíncrona), sagas, consistencia entre A y B.
- Multi-tenant, i18n (la UI es en español), notificaciones (email/SMS).
- TLS, dominio propio, Ingress, WAF, CDN.
- Alta disponibilidad de bases de datos (réplicas, backups automáticos, PITR).
- Observabilidad avanzada (tracing distribuido, métricas Prometheus, dashboards).

## Preguntas abiertas
- **Resuelto 2026-11-17**: sí, dominio Biblioteca. ~~**Q-SYS-1**: el dominio no venía fijado en el enunciado (`{{DOMINIO}}`);
  se asumió "Biblioteca: libros (A) y socios/préstamos (B)". ¿Lo confirmas?~~
- **Resuelto 2026-11-17**: sin autenticación; HTTP y acceso por IP/DNS del LB. ~~**Q-SYS-2**: ¿se requiere autenticación (aunque sea básica en Nginx) para
  exponer el LB público? Hoy está fuera de alcance.~~
