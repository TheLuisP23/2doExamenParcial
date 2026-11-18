# 004 · Plataforma — tareas (modo vía rápida)

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md).
> **2026-11-17 — vía rápida**: tareas consolidadas (desglose original en el commit `24a9bdf`).
> El clúster va primero porque es el camino crítico (~20 min); la access entry se añade tras Terraform.

- [x] **TASK-P-01** — ClusterConfig de eksctl, render y pruebas
  - Tipo: impl
  - Depende de: —
  - REQ: REQ-P-006
  - Archivos: `deploy/eksctl/**`, `scripts/render-cluster-config.sh`, `tests/platform/test_eksctl_config.py`, `tests/platform/conftest.py`, `tests/conftest.py`
  - Hecho cuando: pruebas en verde; `eksctl create cluster --dry-run` sin error; `make verify` verde.

- [x] **TASK-P-02** — Terraform: backend S3, ECR, OIDC, rol IAM + bootstrap del bucket
  - Tipo: impl
  - Depende de: —
  - REQ: REQ-P-003, REQ-P-004, REQ-P-005
  - Archivos: `deploy/terraform/**`, `scripts/tf-backend-bootstrap.sh`, `tests/platform/test_terraform_static.py`
  - Hecho cuando: `terraform fmt/validate` y pruebas en verde; `make verify` verde.

- [x] **TASK-P-03** — Manifiestos Kubernetes, Secrets y render
  - Tipo: impl
  - Depende de: —
  - REQ: REQ-P-007, REQ-P-008, REQ-P-009, REQ-P-010, REQ-P-011, REQ-P-012, REQ-P-017, REQ-SYS-002
  - Archivos: `deploy/k8s/**`, `scripts/k8s-secrets.sh`, `scripts/render-manifests.sh`, `tests/platform/test_k8s_manifests.py`, `tests/system/**`
  - Hecho cuando: kubeconform y pruebas en verde; `make verify` verde.

- [ ] **TASK-P-04** — Pruebas de Dockerfiles y docker compose
  - Tipo: test
  - Depende de: TASK-A-01, TASK-B-01, TASK-F-01
  - REQ: REQ-P-001, REQ-P-002, REQ-SYS-003
  - Archivos: `tests/platform/test_dockerfiles.py`, `tests/platform/test_compose.py`, `docker-compose.yml`, `deploy/local/**`
  - Hecho cuando: `./init.sh --up` deja todo healthy; pruebas en verde; `make verify` verde.

- [x] **TASK-P-05** — Workflows CI/CD
  - Tipo: impl
  - Depende de: TASK-P-02, TASK-P-03
  - REQ: REQ-P-013, REQ-P-014
  - Archivos: `.github/workflows/**`, `tests/platform/test_workflows.py`, `deploy/terraform/main.tf`, `specs/004-plataforma/spec.md`
  - Hecho cuando: pruebas en verde; `make verify` verde.

- [ ] **TASK-P-06** — Smoke tests y scripts de aprovisionamiento/destrucción
  - Tipo: impl
  - Depende de: TASK-P-01, TASK-P-02, TASK-P-03
  - REQ: REQ-P-015, REQ-P-016
  - Archivos: `tests/smoke/**`, `scripts/infra-up.sh`, `scripts/infra-down.sh`, `tests/platform/test_provisioning.py`, `Makefile`
  - Hecho cuando: pruebas en verde; smoke contra el LB en verde; `make verify` verde.

- [ ] **TASK-P-07** — Despliegue real en AWS (operación supervisada)
  - Tipo: ops
  - Depende de: TASK-P-04, TASK-P-05, TASK-P-06
  - REQ: REQ-P-015, REQ-P-016
  - Archivos: `PROGRESS.md`, `docs/runbook.md`
  - Hecho cuando: app accesible por la URL del LB; smoke en verde; URL anotada en PROGRESS.md.

- [ ] **TASK-P-08** — NetworkPolicies (default deny + cada BD solo desde su servicio) y usuario de app en Mongo
  - Tipo: impl
  - Depende de: TASK-P-03
  - REQ: REQ-P-018
  - Archivos: `deploy/k8s/**`, `tests/platform/test_k8s_manifests.py`
  - Hecho cuando: pruebas de políticas en verde; desde un pod de service-b no se alcanza postgres:5432; `make verify` verde.

