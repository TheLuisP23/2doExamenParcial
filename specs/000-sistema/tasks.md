# 000 · Sistema — tareas

> Formato (lo parsean `scripts/task.py` y `scripts/check_traceability.py`):
> `- [ ] **TASK-ID** [P] — título` + viñetas `Tipo`, `Depende de`, `REQ`, `Archivos`, `Hecho cuando`.
> `[P]` = paralelizable con otras `[P]` del mismo nivel. Las casillas solo las marca `make task-done`.
>
> **TDD compatible con "hecho = verify verde"**: una tarea `test` deja sus pruebas en rojo como
> *fallo esperado estricto* — pytest `@pytest.mark.xfail(strict=True, reason="TASK-…")`, Vitest
> `it.fails(...)`, Playwright `test.fail()`. Así `make verify` pasa y la prueba **no puede** pasar
> por accidente (un XPASS estricto falla). La tarea `impl` correspondiente retira el marcador; por eso
> su lista de archivos incluye esas pruebas (solo para quitar el marcador, nunca para debilitarlas).

- [ ] **TASK-S-00** — Scaffold del harness y de la estructura del repositorio
  - Tipo: scaffold
  - Depende de: —
  - REQ: —
  - Archivos: `docker-compose.yml`, `.github/workflows/ci.yml`, `**/README.md`
  - Hecho cuando: `./init.sh --check` sin errores; contratos válidos; `feature_list.json` con todo en `passes: false`; `make verify` verde.

- [ ] **TASK-S-01** [P] — Pruebas de arquitectura: independencia de servicios
  - Tipo: test
  - Depende de: —
  - REQ: REQ-SYS-002
  - Archivos: `tests/system/test_independence.py`, `tests/system/conftest.py`
  - Hecho cuando: las pruebas analizan `services/*`, `.env.example` y `deploy/k8s` y pasan sobre el scaffold; `make verify` verde.

- [ ] **TASK-S-02** [P] — Pruebas de convenciones sobre contratos y configuración
  - Tipo: test
  - Depende de: —
  - REQ: REQ-SYS-003, REQ-SYS-005, REQ-SYS-006
  - Archivos: `tests/system/test_conventions.py`
  - Hecho cuando: verifica que ambos `openapi.yaml` declaran `/health/live`, `/health/ready` y respuestas 4xx `application/problem+json`, y que `.env.example` documenta las variables obligatorias; `make verify` verde.

- [ ] **TASK-S-03** — E2E de sistema: proxy, salud y correlación
  - Tipo: test
  - Depende de: TASK-A-03, TASK-B-03, TASK-F-03, TASK-P-02
  - REQ: REQ-SYS-001, REQ-SYS-003, REQ-SYS-004
  - Archivos: `frontend/e2e/system.spec.ts`
  - Hecho cuando: `make e2e` contra docker compose pasa; `make verify` verde.
