# Biblioteca — interfaz única de comandos del harness.
# Sin `make` (Windows): cada target muestra su equivalente `bash scripts/py.sh scripts/<x>.py`.
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
PY := bash scripts/py.sh
ID ?=
URL ?=

.PHONY: help init check up down verify verify-release lint contracts traceability feature-check \
        status task-list task-start task-done task-abort feature-pass e2e smoke end-session \
        tf-plan cluster-dry-run k8s-validate k8s-bootstrap k8s-secrets deploy infra-up infra-down

help: ## Lista los targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n",$$1,$$2}'

## ── ciclo de vida ───────────────────────────────────────────────────────────
init: ## Verifica herramientas e instala dependencias (./init.sh)
	./init.sh

check: ## Verificación rápida de entorno, sin instalar (./init.sh --check)
	./init.sh --check

up: ## Levanta docker compose y hace smoke test local
	./init.sh --up

down: ## Detiene docker compose
	docker compose down

end-session: ## verify + PROGRESS.md + compose down + árbol git limpio
	$(PY) scripts/end_session.py

## ── verificación ────────────────────────────────────────────────────────────
verify: ## La ÚNICA definición de "hecho"
	$(PY) scripts/verify.py

verify-release: ## verify + trazabilidad total (todos los REQ con test en verde)
	$(PY) scripts/verify.py --release

lint: ## Solo pasos de lint/tipos/tests de los componentes
	$(PY) scripts/verify.py --only service-a,service-b,frontend

contracts: ## Valida los openapi.yaml
	$(PY) scripts/check_contracts.py

traceability: ## Matriz REQ → tests
	$(PY) scripts/check_traceability.py --report

feature-check: ## Valida feature_list.json (esquema + append-only)
	$(PY) scripts/check_feature_list.py

k8s-validate: ## kubeconform sobre deploy/k8s
	$(PY) scripts/verify.py --only k8s

cluster-dry-run: ## eksctl create cluster --dry-run
	$(PY) scripts/verify.py --only eksctl

tf-plan: ## terraform plan (requiere backend.hcl y credenciales; no aplica nada)
	cd deploy/terraform && terraform init -backend-config=backend.hcl -input=false && terraform plan -input=false

e2e: ## Playwright contra docker compose (stack levantado)
	cd frontend && npm run e2e

smoke: ## Smoke tests: make smoke URL=http://<dns-del-lb>
	SMOKE_BASE_URL="$(URL)" $(PY) -m pytest -q tests/smoke

## ── estado y alcance ────────────────────────────────────────────────────────
status: ## Resumen de progreso, tarea activa y próximas features
	$(PY) scripts/status.py

task-list: ## Todas las tareas con estado
	$(PY) scripts/task.py list

task-start: ## Activa una tarea (WIP=1): make task-start ID=TASK-A-01
	@test -n "$(ID)" || (echo "uso: make task-start ID=TASK-…" && exit 2)
	$(PY) scripts/task.py start $(ID)

task-done: ## verify + chequeo de alcance + marca [x]: make task-done ID=TASK-A-01
	@test -n "$(ID)" || (echo "uso: make task-done ID=TASK-…" && exit 2)
	$(PY) scripts/task.py done $(ID)

task-abort: ## Desactiva la tarea activa sin marcarla
	$(PY) scripts/task.py abort

feature-pass: ## Marca una feature como pasada tras verificar: make feature-pass ID=FEAT-A-01
	@test -n "$(ID)" || (echo "uso: make feature-pass ID=FEAT-…" && exit 2)
	$(PY) scripts/feature.py pass $(ID)

## ── plataforma (requieren confirmación humana; scripts en TASK-P-08/P-13) ──
infra-up: ## terraform → eksctl → kubectl bootstrap → secrets (TASK-P-13)
	@test -x scripts/infra-up.sh || (echo "scripts/infra-up.sh pendiente (TASK-P-13)" && exit 1)
	scripts/infra-up.sh

infra-down: ## Orden inverso: LB/namespace → eksctl delete → terraform destroy (TASK-P-13)
	@test -x scripts/infra-down.sh || (echo "scripts/infra-down.sh pendiente (TASK-P-13)" && exit 1)
	scripts/infra-down.sh

k8s-bootstrap: ## Namespace + StorageClass (cluster-admin)
	kubectl apply -f deploy/k8s/bootstrap/

k8s-secrets: ## Crea Secrets en el clúster (TASK-P-08)
	@test -x scripts/k8s-secrets.sh || (echo "scripts/k8s-secrets.sh pendiente (TASK-P-08)" && exit 1)
	scripts/k8s-secrets.sh

deploy: ## Despliegue manual (normalmente lo hace el CD)
	@test -x scripts/render-manifests.sh || (echo "scripts/render-manifests.sh pendiente (TASK-P-08)" && exit 1)
	scripts/render-manifests.sh | kubectl apply -n biblioteca -f -
