---
description: Implementar UNA tarea (WIP=1) con TDD, solo en sus archivos permitidos
argument-hint: <TASK-ID>
---

Implementa **solo** `$ARGUMENTS`. Fases SDD 4-6 (test → código → verify).

1. `make task-start ID=$ARGUMENTS` (o `bash scripts/py.sh scripts/task.py start $ARGUMENTS`).
   Si falla (otra tarea activa, dependencias pendientes) **detente** e informa.
2. Lee la tarea en su `tasks.md`, los REQ que cubre en `spec.md`, el `plan.md` y, si aplica, el contrato
   `contracts/openapi.yaml`. Los archivos permitidos son los que imprimió `task-start`; el hook
   `scope_guard` bloqueará cualquier otro. Si necesitas otro archivo, **para** y propón modificar la tarea.
3. Según el `Tipo`:
   - **test**: delega en el subagente **test-engineer**. Cada prueba referencia su REQ y queda en rojo
     con fallo esperado estricto (`xfail(strict=True)` / `it.fails` / `test.fail()`). Confirma que fallan por la razón correcta.
   - **impl**: escribe el mínimo código para que las pruebas de la tarea `test` previa pasen; retira sus
     marcadores de fallo esperado. No debilites ni borres aserciones.
   - **scaffold / ops**: solo lo descrito en "Hecho cuando".
4. Ejecuta `make verify` hasta que esté en verde. Si no lo consigues, explica el bloqueo en PROGRESS.md › Bloqueos.
5. Revisión: subagente **code-reviewer** (código) y, si tocaste Dockerfile/k8s/eksctl/Terraform/workflows,
   **platform-engineer**. Corrige lo bloqueante y vuelve a verificar.
6. `make task-done ID=$ARGUMENTS` — ejecuta verify, comprueba alcance y marca `[x]`. Tu palabra no cuenta: si falla, no está hecha.
7. Commit pequeño con Conventional Commits incluyendo el ID (el comando sugerido lo imprime `task-done`).
8. Si con esto todas las tareas de una feature quedan hechas: `make feature-pass ID=FEAT-…` y commit.
9. Actualiza PROGRESS.md (Hecho / Siguiente). Una sola tarea por invocación: **no** empieces la siguiente.
