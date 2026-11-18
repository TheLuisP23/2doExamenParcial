# PROGRESS

> Estado legible para humanos. Se actualiza **al final de cada sesión** (secciones manuales) y
> `make end-session` reescribe el bloque automático. El estado máquina vive en `feature_list.json`
> y en las casillas de `specs/*/tasks.md`.

## Sesión
- **N.º**: 1 · **Fecha**: 2026-11-17 · **Agente**: Claude Code
- **Objetivo**: scaffold de harness y especificaciones (sin código de implementación).

## Fase actual
Fase 0 — **Specs y harness en revisión humana**. Ninguna feature implementada (0/47 `passes: true`).

## Hecho
- Estructura del monorepo, `CLAUDE.md`/`AGENTS.md`, constitución v1.0.0.
- Specs 000–004 con REQ (61), historias, Dado/Cuando/Entonces, NFR, fuera de alcance y preguntas abiertas.
- Contratos OpenAPI 3.1 de A (libros) y B (socios/préstamos) + `data-model.md`.
- Planes y `tasks.md` (56 tareas, pruebas antes que implementación).
- Harness: settings (permisos + hooks), 6 comandos, 4 subagentes, scripts de verificación/estado/alcance,
  `init.sh`, `Makefile`, pre-commit, CI, `docs/harness.md`, `docs/architecture.md`, 8 ADRs.
- Validado: `./init.sh --check` (0 errores), ambos `openapi.yaml` válidos (3.1 + reglas de la casa), `feature_list.json` 47 features con `passes: false`, autopruebas del harness en una copia (25/32; las 7 restantes eran rutas estilo Git Bash, ya normalizadas en los hooks).

## En curso
- Nada (sin tarea activa).

## Siguiente
1. **Humano**: revisar specs y responder las preguntas `[NEEDS CLARIFICATION]` (lista en el resumen de la sesión 1).
2. Ejecutar `./init.sh` completo (crea `.venv-tools`, instala pre-commit, copia `.env`).
3. Tareas listas para empezar (en paralelo, WIP=1 por agente): `TASK-S-01`, `TASK-S-02`, `TASK-A-01`,
   `TASK-B-01`, `TASK-F-01`, `TASK-P-01`, `TASK-P-03`, `TASK-P-05`, `TASK-P-07`, `TASK-P-09`, `TASK-P-11`, `TASK-P-12`.

## TODO (pendiente por falta de tiempo en la sesión 1)
- [ ] Cerrar `TASK-S-00` con `make task-done ID=TASK-S-00` (se abortó para editar la spec; sus archivos ya existen).
- [ ] Re-ejecutar las autopruebas del harness tras normalizar rutas en los hooks (scope_guard/post_edit/stop).
- [ ] Ejecutar `./init.sh` completo (crea `.venv-tools`, instala pre-commit, copia `.env`) — el clasificador de modo auto lo bloqueó; requiere que lo ejecute un humano.
- [ ] `make verify` completo en el repo real (verificado solo en la copia: VERDE con SKIP de componentes sin crear).
- [ ] Revisión con el subagente `spec-reviewer` de las specs 000–004.
- [ ] Fijar acciones de GitHub por SHA en `ci.yml` (TASK-P-10).
- [ ] Instalar `uv`, `make`, `kubeconform`, `gitleaks` localmente; arrancar Docker Desktop.

## Bloqueos
- Preguntas abiertas que afectan al diseño: Q-SYS-1 (dominio), Q-B-5 (versión de Node), Q-P-1 (`owner/repo` para OIDC), Q-P-2 (bucket de estado).
- `make` y `uv` no están instalados en la máquina local (Windows): usar `bash scripts/py.sh scripts/…` y `pip install uv`.

## Decisiones
- Dominio asumido: Biblioteca — A = catálogo de libros, B = socios + préstamos (`book_id` opaco).
- Kubernetes 1.36 en EKS (eksctl 0.231 acepta 1.31–1.37).
- Node 22 LTS en el plan de B (Node 20 está EOL) — pendiente de confirmación (Q-B-5).
- Trazabilidad por alcance + TDD con xfail estricto ([ADR-0008](docs/adr/0008-verificacion-incremental.md)).
- CI tiene `AmazonEKSEditPolicy` limitada al namespace `biblioteca`; namespace y StorageClass los aplica el operador.
- Backend de Terraform con bloqueo nativo de S3 (`use_lockfile`), sin DynamoDB.

## Último cierre automático
<!-- AUTO:BEGIN (lo escribe scripts/end_session.py; no editar a mano) -->
- Aún no se ha ejecutado `make end-session`.
<!-- AUTO:END -->
