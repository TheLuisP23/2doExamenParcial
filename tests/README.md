# tests/ — pruebas transversales (pytest)

| Carpeta | Qué | Tareas |
|---|---|---|
| `system/` | arquitectura e invariantes del sistema (independencia, convenciones) | TASK-S-01, TASK-S-02 |
| `platform/` | Dockerfiles, compose, Terraform, eksctl, manifiestos k8s, workflows | TASK-P-01, P-03, P-05, P-07, P-09, P-12 |
| `smoke/` | post-deploy contra `SMOKE_BASE_URL` (se salta si no está definida) | TASK-P-11 |

Cada test referencia sus requisitos con `@pytest.mark.req("REQ-…")` (lo exige `scripts/check_traceability.py`).
Las pruebas de cada servicio viven dentro del servicio (`services/*/tests`, `frontend/tests`, `frontend/e2e`).
