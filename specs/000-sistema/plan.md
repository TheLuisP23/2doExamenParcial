# 000 · Sistema — plan técnico

## Topología
```
navegador ──HTTP:80──▶ LB AWS ──▶ Service LoadBalancer ──▶ Nginx (frontend, :8080)
                                         ├─ /            → SPA estática (index.html fallback)
                                         ├─ /api/a/*     → service-a:8000 (prefijo eliminado)
                                         └─ /api/b/*     → service-b:3000 (prefijo eliminado)
service-a ──▶ postgres:5432 (StatefulSet, PVC gp3)
service-b ──▶ mongo:27017   (StatefulSet, PVC gp3)
```
Detalle C4 en [docs/architecture.md](../../docs/architecture.md).

## Convenciones transversales
| Tema | Decisión |
|---|---|
| Puertos | A `8000`, B `3000`, Nginx `8080` (no-root); LB expone `80` → `8080` |
| Salud | `/health/live`, `/health/ready` → `{"status":"ok"\|"unavailable","checks":{...}}` |
| Errores | RFC 9457 `application/problem+json`; `type` = `about:blank` o URI relativa `/problems/<slug>` |
| IDs | UUID v4 en string para todas las entidades (A y B) |
| Fechas | RFC 3339 en UTC (`2026-11-17T10:00:00Z`); fechas sin hora `YYYY-MM-DD` |
| Paginación | `?limit=20&offset=0` (máx. `limit=100`); respuesta `{items, total, limit, offset}` |
| Correlación | `X-Request-ID` (Nginx `$request_id` si falta); log JSON `request_id` |
| Config | prefijos `SERVICE_A_*`, `SERVICE_B_*`; ver `.env.example` |
| Logs | JSON a stdout: `timestamp, level, message, service, request_id, method, path, status, duration_ms` |

## Estrategia de pruebas transversales
| Nivel | Dónde | Qué cubre |
|---|---|---|
| Arquitectura (estática) | `tests/system/test_independence.py` | REQ-SYS-002 |
| Convenciones (estática sobre contratos/config) | `tests/system/test_conventions.py` | REQ-SYS-003, 005, 006 |
| E2E sistema (Playwright, stack compose) | `frontend/e2e/system.spec.ts` | REQ-SYS-001, 003, 004 |
| Smoke post-deploy | `tests/smoke/test_smoke.py` | REQ-SYS-001, REQ-SYS-003 en EKS |

Cada prueba lleva el ID del requisito: en pytest `@pytest.mark.req("REQ-SYS-002")`, en TS el
título contiene `[REQ-SYS-001]`. `scripts/check_traceability.py` lo exige.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| El front hace demasiada composición (préstamo = socio + libro) | Mantener composición en hooks de datos simples; sin lógica de negocio de B en el front |
| `book_id` inválido en préstamos (B no valida contra A) | El front solo ofrece libros listados desde A; documentado como consistencia eventual aceptada |
| Coste AWS si el clúster queda encendido | `make infra-down` + recordatorio en `make end-session` |
