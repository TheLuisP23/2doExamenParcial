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

- [ ] **TASK-S-01** — Pruebas de sistema: independencia y convenciones
  - Tipo: test
  - Depende de: —
  - REQ: REQ-SYS-002, REQ-SYS-003, REQ-SYS-005, REQ-SYS-006
  - Archivos: `tests/system/**`, `tests/conftest.py`
  - Hecho cuando: pruebas en verde; `make verify` verde.
