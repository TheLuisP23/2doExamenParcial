# Biblioteca — monorepo SDD + harness para agentes

Proyecto académico con dos microservicios independientes, un frontend y despliegue en AWS EKS,
construido con **Spec-Driven Development** y un **harness** para agentes de IA.

| Componente | Stack | Base de datos | Ruta pública |
|---|---|---|---|
| Servicio A — catálogo de libros | Python 3.12 · FastAPI | PostgreSQL 16 | `/api/a/*` |
| Servicio B — socios y préstamos | Node.js · TypeScript · Express | MongoDB 7 | `/api/b/*` |
| Frontend | React · Vite · TypeScript · Nginx | — | `/` |

Despliegue: Terraform (ECR, OIDC, IAM) → eksctl (clúster EKS) → kubectl (YAML planos).
CI/CD con GitHub Actions autenticado por OIDC. Exposición solo HTTP vía DNS del LoadBalancer.

## Estado
Fase actual: **scaffold de harness y specs** (sin código de implementación). Ver
[PROGRESS.md](PROGRESS.md) y `make status`.

## Empezar
```bash
cp .env.example .env      # valores locales (no se versiona)
./init.sh                 # verifica herramientas, instala dependencias
./init.sh --up            # además levanta docker compose y hace smoke test
make verify               # la definición de "hecho"
```
En Windows sin `make`, usa `bash scripts/py.sh scripts/verify.py` (los targets del
[Makefile](Makefile) muestran el comando equivalente).

## Documentación
- [specs/constitution.md](specs/constitution.md) — principios
- [specs/](specs/) — especificaciones por componente
- [docs/architecture.md](docs/architecture.md) — C4
- [docs/harness.md](docs/harness.md) — los 5 subsistemas del harness
- [docs/adr/](docs/adr/README.md) — decisiones de arquitectura
- [CLAUDE.md](CLAUDE.md) / [AGENTS.md](AGENTS.md) — instrucciones para agentes
