# 0008 — Verificación incremental: trazabilidad por alcance y TDD con xfail estricto

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: constitución IV, docs/harness.md

## Contexto
Dos reglas chocan: "una tarea solo está hecha si `make verify` pasa" y "verify falla si un REQ no tiene
test". Aplicada literalmente a todos los REQ, la segunda haría fallar verify hasta la última tarea, y
ninguna tarea intermedia podría cerrarse. Además, TDD exige pruebas en rojo antes del código.

## Decisión
1. **Trazabilidad por alcance**: `check_traceability.py` exige test para los REQ *en alcance*: los REQ
   de tareas marcadas `[x]` y de features con `passes: true`. `--all` (usado por `make verify-release`)
   exige todos. La regla inversa (todo test referencia un REQ existente) es siempre estricta.
2. **Rojo controlado**: las tareas `test` marcan sus pruebas como fallo esperado *estricto*
   (`xfail(strict=True)`, `it.fails`, `test.fail()`); verify pasa, y un XPASS rompe el build, lo que
   obliga a la tarea `impl` a retirar el marcador.
3. **Componentes aún no creados**: verify marca como SKIP (visible en el resumen) los pasos cuyo
   manifiesto (`pyproject.toml`, `package.json`, `*.tf`, `cluster.yaml`) no existe todavía. Cuando la
   tarea scaffold de un componente está marcada `[x]`, su ausencia pasa a ser FAIL.

## Consecuencias
- (+) Cada tarea puede cerrarse en verde sin rebajar el estándar final.
- (−) Un REQ podría quedar sin test hasta que se cierre su tarea → `make verify-release` lo detecta.
