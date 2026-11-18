# CLAUDE.md — punto de entrada para agentes

Biblioteca: **servicio A** (catálogo de libros · Python/FastAPI/PostgreSQL) y **servicio B**
(socios y préstamos · Node/TypeScript/Express/MongoDB), **frontend** React servido por Nginx
(proxy `/api/a`, `/api/b`) y despliegue en **AWS EKS**. Proyecto académico con SDD + harness.

Este archivo es un **mapa**, no el manual. Lee lo enlazado solo cuando lo necesites.

## Antes de nada
1. La sesión arranca con `./init.sh --check` (hook SessionStart). Lee su salida.
2. Lee [PROGRESS.md](PROGRESS.md) y ejecuta `/status`.
3. Principios no negociables: [specs/constitution.md](specs/constitution.md).

## Mapa del repo
| Ruta | Qué hay |
|---|---|
| `specs/000-sistema` … `004-plataforma` | spec → plan → tasks (+ data-model y contracts en A/B) |
| `docs/architecture.md` · `docs/harness.md` · `docs/adr/` | arquitectura C4, harness, decisiones |
| `services/service-a`, `services/service-b`, `frontend/` | código (solo tras una tarea activa) |
| `deploy/eksctl`, `deploy/terraform`, `deploy/k8s` | infraestructura |
| `scripts/` | verificación, trazabilidad, estado, tareas |
| `tests/system`, `tests/platform`, `tests/smoke` | pruebas transversales |
| `feature_list.json` · `PROGRESS.md` | estado (máquina · humano) |

## Flujo obligatorio
`spec → plan → tasks → test → código → verify` — comandos `/spec`, `/plan`, `/tasks`,
`/implement <TASK-ID>`, `/verify`, `/status`. Nunca escribas código sin una tarea activa.

## Comandos
```
./init.sh [--check|--up]   # arranque de sesión (idempotente)
make verify                # ÚNICA definición de "hecho"
make status                # progreso + próximas features
make task-start ID=TASK-A-01 / make task-done ID=TASK-A-01
make up / make down / make e2e / make smoke URL=http://<lb-dns>
make end-session           # verify + PROGRESS + down + árbol limpio
```
Sin `make` (Windows): `bash scripts/py.sh scripts/verify.py` etc. (ver [Makefile](Makefile)).

## Reglas duras
- **WIP = 1**: una tarea activa; solo editas los archivos que lista en su `tasks.md`.
- **Tests primero**; cada test referencia un `REQ-*` y cada REQ en alcance tiene test.
- **"Hecho" = `make verify` en verde.** Tu palabra no cuenta.
- `feature_list.json`: solo puedes cambiar `passes` a `true` vía `make feature-pass`, tras verificar. Nunca borres ni reescribas entradas.
- Servicios independientes: sin BD, código ni llamadas compartidas entre A y B.
- Sin secretos en el repo; no leas `.env` ni `~/.aws/credentials`.
- Ambigüedad → `[NEEDS CLARIFICATION]` en la spec y pregunta; no inventes.
- `terraform apply/destroy`, `eksctl create/delete`, `kubectl apply/delete`, `git push`: requieren confirmación humana.
- Commits pequeños, Conventional Commits (`feat(a): ... [TASK-A-03]`).
- Al cerrar sesión: actualiza PROGRESS.md y corre `make end-session`.

## Enlaces
- Constitución: [specs/constitution.md](specs/constitution.md)
- Sistema: [specs/000-sistema/spec.md](specs/000-sistema/spec.md)
- Harness (5 subsistemas): [docs/harness.md](docs/harness.md)
- Arquitectura: [docs/architecture.md](docs/architecture.md) · ADRs: [docs/adr/](docs/adr/README.md)
- Subagentes: `.claude/agents/` (spec-reviewer, test-engineer, code-reviewer, platform-engineer)
