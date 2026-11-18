---
description: Crear o refinar la spec de un componente (qué y por qué, nunca cómo)
argument-hint: <000-sistema|001-servicio-a|002-servicio-b|003-frontend|004-plataforma> [tema]
---

Vas a trabajar en la **spec** de `specs/$ARGUMENTS`. Fase SDD 1/6: no escribas código, plan ni tareas.

1. Lee `specs/constitution.md`, `specs/000-sistema/spec.md` y la spec destino si existe.
2. Escribe/actualiza `spec.md` siguiendo la estructura de las specs existentes:
   - Encabezado (estado, versión, fecha, enlaces).
   - Historias de usuario `HU-X-NN (P1|P2|P3)`.
   - Requisitos `### REQ-X-NNN — Título (Pn)` con criterios **Dado / Cuando / Entonces** verificables.
     IDs nuevos al final; **nunca** renumeres ni reutilices un ID existente.
   - Requisitos no funcionales con "Verificado por".
   - **Fuera de alcance** (obligatorio).
   - **Preguntas abiertas** con `[NEEDS CLARIFICATION]` para todo lo ambiguo. No inventes reglas de negocio.
3. Si el componente tiene API, actualiza `contracts/openapi.yaml` (contrato primero) y `data-model.md`.
   Cada operación cita sus `REQ-*` en `summary`.
4. Añade al **final** de `feature_list.json` las features nuevas que cubran los REQ nuevos
   (`passes: false`, `verified_at: null`, `verified_commit: null`). No modifiques entradas existentes.
5. Ejecuta `bash scripts/py.sh scripts/check_contracts.py` y `bash scripts/py.sh scripts/check_feature_list.py`.
6. Lanza el subagente **spec-reviewer** sobre la spec y aplica sus observaciones bloqueantes.
7. Resume los cambios y **lista las preguntas `[NEEDS CLARIFICATION]` al usuario**. Detente.
