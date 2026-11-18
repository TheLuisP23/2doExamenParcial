---
description: Estado del proyecto - progreso, tarea activa, próximas tareas y features
---

1. Ejecuta `bash scripts/py.sh scripts/status.py` y `bash scripts/py.sh scripts/task.py list`.
2. Ejecuta `git status --short` y `git log --oneline -5`.
3. Responde en ≤ 15 líneas:
   - Fase actual y tarea activa (si la hay).
   - Progreso (tareas hechas / total por spec; features con `passes: true`).
   - Último `make verify` (verde/rojo, cuándo).
   - Las 3 próximas tareas listas, indicando cuáles son `[P]`.
   - Bloqueos y preguntas `[NEEDS CLARIFICATION]` abiertas que impiden avanzar.
   - Recomendación concreta: el siguiente `/implement TASK-…` o la pregunta a resolver.
No modifiques archivos.
