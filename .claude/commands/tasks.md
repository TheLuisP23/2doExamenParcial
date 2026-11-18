---
description: Descomponer un plan en tareas atómicas con archivos permitidos
argument-hint: <carpeta de spec, p. ej. 002-servicio-b>
---

Fase SDD 3/6 para `specs/$ARGUMENTS`. No escribas código.

Escribe/actualiza `tasks.md` respetando **exactamente** el formato que parsea `scripts/task.py`
(ver la cabecera de `specs/000-sistema/tasks.md`):

```
- [ ] **TASK-X-NN** [P] — Título
  - Tipo: scaffold | test | impl | ops
  - Depende de: TASK-…, TASK-… | —
  - REQ: REQ-…, REQ-… | —
  - Archivos: `ruta/exacta`, `carpeta/**`
  - Hecho cuando: criterio observable; `make verify` verde.
```

Reglas:
- Atómicas (≤ ~½ día), una responsabilidad. **Cada `impl` tiene antes una `test`** que cubre los mismos REQ.
- Las tareas `test` dejan las pruebas en rojo con fallo esperado estricto; la `impl` lista esas pruebas
  en sus Archivos para retirar el marcador.
- `Archivos` es la frontera de alcance que impone el hook `scope_guard`: sé preciso; usa `**` solo dentro de carpetas propias del componente.
- `[P]` solo si no comparte archivos con otra tarea pendiente del mismo nivel.
- Todo REQ de la spec debe aparecer en alguna tarea `test`.
- **No** marques casillas: solo `make task-done` lo hace.

Al terminar: `bash scripts/py.sh scripts/task.py lint` y `bash scripts/py.sh scripts/task.py list`. Resume y detente.
