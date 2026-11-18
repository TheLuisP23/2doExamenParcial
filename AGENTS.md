# AGENTS.md — instrucciones para cualquier agente de código

> Equivalente agnóstico de [CLAUDE.md](CLAUDE.md). Si tu herramienta no soporta hooks ni
> slash-commands, ejecuta tú mismo los pasos que esos mecanismos automatizan (indicados abajo).

## Propósito
Monorepo académico: catálogo de libros (servicio A, Python/FastAPI/PostgreSQL), socios y
préstamos (servicio B, Node/TS/Express/MongoDB), frontend React+Nginx y despliegue en AWS EKS.
Se construye con Spec-Driven Development: las specs en `specs/` son la fuente de verdad.

## Inicio de sesión (lo que hace el hook SessionStart)
```
./init.sh --check          # herramientas, credenciales AWS, resumen de estado
make status                # o: bash scripts/py.sh scripts/status.py
```
Luego lee `PROGRESS.md`.

## Mapa
- `specs/constitution.md` — principios no negociables.
- `specs/NNN-*/spec.md|plan.md|tasks.md` — qué, cómo y en qué orden.
- `specs/001-servicio-a/contracts/openapi.yaml`, `specs/002-servicio-b/contracts/openapi.yaml` — contratos.
- `docs/harness.md` — cómo funciona el harness; `docs/architecture.md`; `docs/adr/`.
- `feature_list.json` (estado máquina) · `PROGRESS.md` (estado humano).

## Flujo obligatorio
1. **spec** → requisitos con ID `REQ-*`, Dado/Cuando/Entonces, Fuera de alcance.
2. **plan** → stack, capas, estrategia de pruebas.
3. **tasks** → tareas atómicas `TASK-*` con archivos permitidos.
4. **test** → escribe pruebas que fallen y referencien sus `REQ-*`.
5. **código** → mínimo para pasar.
6. **verify** → `make verify` (o `bash scripts/py.sh scripts/verify.py`).

Para implementar: `make task-start ID=<TASK-ID>` → trabajar → `make task-done ID=<TASK-ID>`
(este último ejecuta verify y marca la casilla). Solo una tarea activa a la vez.

## Reglas duras
- Solo toca los archivos listados en la tarea activa (lo que hace el hook PreToolUse `scope_guard`).
- Tras editar, formatea/lintea (lo que hace el hook PostToolUse `post_edit`).
- Antes de terminar, `make verify` (lo que hace el hook Stop).
- No modifiques ni borres entradas de `feature_list.json`; solo `make feature-pass ID=...`.
- Nunca leas ni escribas `.env` reales ni `~/.aws/credentials`. Nunca subas secretos.
- No ejecutes `terraform apply/destroy`, `eksctl create/delete`, `kubectl apply/delete` ni
  `git push` sin aprobación humana explícita.
- Conventional Commits, commits pequeños con el TASK-ID.
- Cierra con `make end-session` y deja el árbol git limpio.
