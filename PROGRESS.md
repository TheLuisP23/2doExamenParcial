# PROGRESS

> Estado legible para humanos. Se actualiza **al final de cada sesión** (secciones manuales) y
> `make end-session` reescribe el bloque automático. El estado máquina vive en `feature_list.json`
> y en las casillas de `specs/*/tasks.md`.

## Sesión
- **N.º**: 1 · **Fecha**: 2026-11-17 · **Agente**: Claude Code
- **Objetivo**: scaffold de harness y especificaciones (sin código de implementación).

## Fase actual
Fase 2 — **DESPLEGADO en AWS EKS** (2026-11-17 22:42).
- **URL pública**: http://a2384f55c9dcd4efcb511803a26b72d2-635917248.us-east-1.elb.amazonaws.com
- Clúster `biblioteca-eks` (1.37, 2×t3.medium, us-east-1) · ECR `423623848858.dkr.ecr.us-east-1.amazonaws.com/biblioteca/*:f1e24f8`
- Smoke manual OK: health de front/A/B, alta de libro (A), socio (B), préstamo (B), búsqueda sin acentos.

## Hecho
- Estructura del monorepo, `CLAUDE.md`/`AGENTS.md`, constitución v1.0.0.
- Specs 000–004 con REQ (61), historias, Dado/Cuando/Entonces, NFR, fuera de alcance y preguntas abiertas.
- Contratos OpenAPI 3.1 de A (libros) y B (socios/préstamos) + `data-model.md`.
- Planes y `tasks.md` (56 tareas, pruebas antes que implementación).
- Harness: settings (permisos + hooks), 6 comandos, 4 subagentes, scripts de verificación/estado/alcance,
  `init.sh`, `Makefile`, pre-commit, CI, `docs/harness.md`, `docs/architecture.md`, 8 ADRs.
- Validado: `./init.sh --check` (0 errores), ambos `openapi.yaml` válidos (3.1 + reglas de la casa), `feature_list.json` 47 features con `passes: false`, autopruebas del harness en una copia (25/32; las 7 restantes eran rutas estilo Git Bash, ya normalizadas en los hooks).

## En curso
- Cierre formal (verify) de TASK-F-01, TASK-P-02, TASK-P-03; luego TASK-P-05 (CD).
- Repo público creado: https://github.com/TheLuisP23/2doExamenParcial (variables AWS_ROLE_ARN, AWS_REGION, EKS_CLUSTER_NAME configuradas).
- Pendiente: actualizar la trust policy del rol IAM a `repo:TheLuisP23/2doExamenParcial:ref:refs/heads/main` (el nombre del repo cambió).

## Siguiente
1. **Humano**: revisar specs y responder las preguntas `[NEEDS CLARIFICATION]` (lista en el resumen de la sesión 1).
2. Ejecutar `./init.sh` completo (crea `.venv-tools`, instala pre-commit, copia `.env`).
3. Tareas listas para empezar (en paralelo, WIP=1 por agente): `TASK-S-01`, `TASK-S-02`, `TASK-A-01`,
   `TASK-B-01`, `TASK-F-01`, `TASK-P-01`, `TASK-P-03`, `TASK-P-05`, `TASK-P-07`, `TASK-P-09`, `TASK-P-11`, `TASK-P-12`.

## TODO (pendiente tras el despliegue)
- [ ] Cerrar con `make task-done`: TASK-F-01 (activa), TASK-P-02 y TASK-P-03 (código aplicado y probado; falta el verify formal).
- [ ] TASK-P-05: workflow CD (`.github/workflows/cd.yml`) + crear repo `TheLuisP23/biblioteca-sdd-eks` y `git push`.
- [ ] TASK-P-04 (tests Dockerfiles/compose), TASK-P-06 (smoke automatizado + infra-up/down), TASK-S-01, TASK-F-02 (E2E).
- [ ] NetworkPolicies (REQ-P-018) y usuario de app en Mongo (hoy B usa root).
- [ ] El build de Docker del front copia `dist/` precompilado (no multi-stage) por la lentitud de npm dentro de Docker.
- [ ] Revisar fallo intermitente de integración de A cuando Docker está cargado.
- [ ] **Coste**: al terminar el examen, destruir: `kubectl delete ns biblioteca` → `eksctl delete cluster -f .harness/cluster.rendered.yaml --wait` → `terraform destroy`.

## Bloqueos
- Preguntas abiertas que afectan al diseño: Q-SYS-1 (dominio), Q-B-5 (versión de Node), Q-P-1 (`owner/repo` para OIDC), Q-P-2 (bucket de estado).
- `make` y `uv` no están instalados en la máquina local (Windows): usar `bash scripts/py.sh scripts/…` y `pip install uv`.

## Decisiones
- Repo GitHub **público** `TheLuisP23/2doExamenParcial` (decisión del usuario, sustituye a `biblioteca-sdd-eks`).
- Se añadió prueba de la plantilla Nginx (REQ-F-008) tras detectarla la trazabilidad.
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
