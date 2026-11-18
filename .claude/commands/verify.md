---
description: Ejecutar la verificación completa e interpretar el resultado
argument-hint: "[--release]"
---

1. Ejecuta `make verify` (sin `make`: `bash scripts/py.sh scripts/verify.py $ARGUMENTS`).
2. Lee el **RESUMEN** final. Para cada `FAIL`, localiza la causa en la salida del paso y propón la
   corrección mínima. Para cada `SKIP`, indica qué tarea lo convertirá en un paso real.
3. Ejecuta también `bash scripts/py.sh scripts/check_traceability.py --report` y señala los REQ en alcance sin test
   y los tests en rojo pendientes.
4. No declares nada como "hecho" si el resultado es ROJO. No marques tareas ni features desde aquí.
5. Responde con: estado (VERDE/ROJO), tabla de fallos → causa → acción, y siguiente paso recomendado.
