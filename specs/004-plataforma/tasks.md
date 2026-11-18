# 004 · Plataforma — tareas

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md). Pruebas antes que implementación.
> Revisión obligatoria del subagente `platform-engineer` antes de `make task-done` en tareas `impl`.

- [ ] **TASK-P-01** [P] — Pruebas: Dockerfiles y docker compose
  - Tipo: test
  - Depende de: —
  - REQ: REQ-P-001, REQ-P-002
  - Archivos: `tests/platform/test_dockerfiles.py`, `tests/platform/test_compose.py`, `tests/platform/conftest.py`
  - Hecho cuando: pruebas en rojo (xfail estricto) para lo que aún no existe; `make verify` verde.

- [ ] **TASK-P-02** — Implementación: Dockerfiles, .dockerignore y ajuste de compose
  - Tipo: impl
  - Depende de: TASK-P-01, TASK-A-03, TASK-B-03, TASK-F-03
  - REQ: REQ-P-001, REQ-P-002
  - Archivos: `services/service-a/Dockerfile`, `services/service-a/.dockerignore`, `services/service-b/Dockerfile`, `services/service-b/.dockerignore`, `frontend/Dockerfile`, `frontend/.dockerignore`, `docker-compose.yml`, `deploy/local/**`, `tests/platform/test_dockerfiles.py`, `tests/platform/test_compose.py`
  - Hecho cuando: `./init.sh --up` deja todo `healthy`; pruebas de P-01 en verde; `make verify` verde.

- [ ] **TASK-P-03** [P] — Pruebas: Terraform (backend, ECR, OIDC, IAM)
  - Tipo: test
  - Depende de: —
  - REQ: REQ-P-003, REQ-P-004, REQ-P-005
  - Archivos: `tests/platform/test_terraform_static.py`, `deploy/terraform/tests/ecr.tftest.hcl`, `deploy/terraform/tests/iam.tftest.hcl`
  - Hecho cuando: pruebas en rojo; `make verify` verde.

- [ ] **TASK-P-04** — Implementación: Terraform + bootstrap del backend
  - Tipo: impl
  - Depende de: TASK-P-03
  - REQ: REQ-P-003, REQ-P-004, REQ-P-005
  - Archivos: `deploy/terraform/*.tf`, `deploy/terraform/backend.hcl.example`, `deploy/terraform/terraform.tfvars.example`, `deploy/terraform/.terraform.lock.hcl`, `deploy/terraform/README.md`, `scripts/tf-backend-bootstrap.sh`, `tests/platform/test_terraform_static.py`, `deploy/terraform/tests/*.tftest.hcl`
  - Hecho cuando: `terraform fmt -check`, `validate`, `test` pasan; `terraform plan` revisado por humano; `make verify` verde.

- [ ] **TASK-P-05** [P] — Pruebas: ClusterConfig de eksctl
  - Tipo: test
  - Depende de: —
  - REQ: REQ-P-006
  - Archivos: `tests/platform/test_eksctl_config.py`
  - Hecho cuando: pruebas en rojo (versión, nodegroup, addons, access entry con scope de namespace, sin ID de cuenta literal).

- [ ] **TASK-P-06** — Implementación: cluster.yaml y render
  - Tipo: impl
  - Depende de: TASK-P-05
  - REQ: REQ-P-006
  - Archivos: `deploy/eksctl/cluster.yaml`, `deploy/eksctl/README.md`, `scripts/render-cluster-config.sh`, `tests/platform/test_eksctl_config.py`
  - Hecho cuando: `eksctl create cluster -f .harness/cluster.rendered.yaml --dry-run` sin error; `make verify` verde.

- [ ] **TASK-P-07** [P] — Pruebas: manifiestos Kubernetes
  - Tipo: test
  - Depende de: —
  - REQ: REQ-P-007, REQ-P-008, REQ-P-009, REQ-P-010, REQ-P-011, REQ-P-012, REQ-P-017, REQ-P-018, REQ-SYS-002
  - Archivos: `tests/platform/test_k8s_manifests.py`
  - Hecho cuando: pruebas en rojo (requests/limits en todo contenedor, probes, securityContext, un único LoadBalancer, sin Secrets reales, labels, NetworkPolicies).

- [ ] **TASK-P-08** — Implementación: manifiestos y script de Secrets
  - Tipo: impl
  - Depende de: TASK-P-07
  - REQ: REQ-P-007, REQ-P-008, REQ-P-009, REQ-P-010, REQ-P-011, REQ-P-012, REQ-P-017, REQ-P-018
  - Archivos: `deploy/k8s/**`, `scripts/k8s-secrets.sh`, `scripts/render-manifests.sh`, `tests/platform/test_k8s_manifests.py`
  - Hecho cuando: kubeconform (`-strict`, versión 1.36) y pruebas de P-07 pasan; `make verify` verde.

- [ ] **TASK-P-09** [P] — Pruebas: workflows de GitHub Actions
  - Tipo: test
  - Depende de: —
  - REQ: REQ-P-013, REQ-P-014
  - Archivos: `tests/platform/test_workflows.py`
  - Hecho cuando: pruebas en rojo (OIDC, sin access keys, acciones fijadas por SHA, permisos mínimos, concurrency).

- [ ] **TASK-P-10** — Implementación: workflow CD (y ajustes a CI)
  - Tipo: impl
  - Depende de: TASK-P-09, TASK-P-08, TASK-P-04
  - REQ: REQ-P-013, REQ-P-014
  - Archivos: `.github/workflows/cd.yml`, `.github/workflows/ci.yml`, `tests/platform/test_workflows.py`
  - Hecho cuando: pruebas de P-09 en verde; actionlint sin errores (si está instalado); `make verify` verde.

- [ ] **TASK-P-11** — Smoke tests post-deploy
  - Tipo: test
  - Depende de: —
  - REQ: REQ-P-015, REQ-SYS-001, REQ-SYS-003
  - Archivos: `tests/smoke/test_smoke.py`, `tests/smoke/conftest.py`
  - Hecho cuando: se saltan sin `SMOKE_BASE_URL`; con el stack local (`SMOKE_BASE_URL=http://localhost:8080`) pasan tras TASK-P-02; `make verify` verde.

- [ ] **TASK-P-12** [P] — Pruebas: orden de aprovisionamiento/destrucción
  - Tipo: test
  - Depende de: —
  - REQ: REQ-P-016
  - Archivos: `tests/platform/test_provisioning.py`
  - Hecho cuando: pruebas en rojo que verifican el orden de pasos en `scripts/infra-up.sh` / `scripts/infra-down.sh`.

- [ ] **TASK-P-13** — Implementación: scripts infra-up / infra-down
  - Tipo: impl
  - Depende de: TASK-P-12, TASK-P-04, TASK-P-06, TASK-P-08
  - REQ: REQ-P-016
  - Archivos: `scripts/infra-up.sh`, `scripts/infra-down.sh`, `Makefile`, `tests/platform/test_provisioning.py`
  - Hecho cuando: pruebas de P-12 en verde; cada paso destructivo pide confirmación; `make verify` verde.

- [ ] **TASK-P-14** — Primer despliegue real en AWS (operación supervisada)
  - Tipo: ops
  - Depende de: TASK-P-13, TASK-P-10, TASK-P-11, TASK-F-12
  - REQ: REQ-P-015, REQ-P-016
  - Archivos: `PROGRESS.md`, `docs/runbook.md`
  - Hecho cuando: un humano aprueba y ejecuta `make infra-up`; CD despliega; `make smoke URL=http://<lb-dns>` verde; URL y evidencias anotadas en PROGRESS.md; `make infra-down` documentado.
