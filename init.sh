#!/usr/bin/env bash
# init.sh — arranque de sesión (subsistema de Ciclo de vida). Idempotente.
#
#   ./init.sh            verifica herramientas + instala dependencias + smoke (si hay stack) + resumen
#   ./init.sh --check    solo verificación rápida (sin instalar); lo ejecuta el hook SessionStart
#   ./init.sh --up       como el modo por defecto y además levanta docker compose
#
# Pasos: 1) herramientas/versiones + aws sts  2) dependencias  3) docker compose (--up)
#        4) smoke de salud  5) resumen de PROGRESS.md y próximas features con passes=false
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
MODE="full"
UP=0
for arg in "$@"; do
  case "$arg" in
    --check) MODE="check" ;;
    --up) UP=1 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "opción desconocida: $arg" >&2; exit 2 ;;
  esac
done

ERRORS=0
WARNINGS=0
# En CI (sin credenciales AWS ni eksctl) las herramientas de infraestructura son opcionales.
INFRA=req
[ -n "${CI:-}" ] && INFRA=opt
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; WARNINGS=$((WARNINGS+1)); }
fail() { printf '  \033[31m✗\033[0m %s\n' "$*"; ERRORS=$((ERRORS+1)); }
hdr()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

# Python real (evita el alias de Microsoft Store)
PY=""
for c in python3 python; do
  if have "$c" && "$c" -c 'import sys' >/dev/null 2>&1; then PY="$c"; break; fi
done

ver() { # ver <cmd> <args...> → primera línea con un número de versión
  "$@" 2>&1 | grep -Eo '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1
}
ge() { # ge <actual> <mínima>  (comparación semver simple)
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ]
}
need() { # need <nombre> <requerida|opcional> <min> <cmd-version...>
  local name="$1" kind="$2" min="$3"; shift 3
  if ! have "$name"; then
    if [ "$kind" = req ]; then fail "$name no instalado (mínimo $min)"; else warn "$name no instalado (opcional)"; fi
    return 1
  fi
  local v; v="$(ver "$@")"
  if [ -n "$min" ] && [ -n "$v" ] && ! ge "$v" "$min"; then
    if [ "$kind" = req ]; then fail "$name $v < $min"; else warn "$name $v < $min"; fi
    return 1
  fi
  ok "$name ${v:-?}"
}

# ─── 1. herramientas ─────────────────────────────────────────────────────────
hdr "1/5 Herramientas"
if [ -n "$PY" ]; then
  PV="$(ver "$PY" --version)"
  if [[ "$PV" == 3.12* ]]; then ok "python $PV"; else warn "python $PV (el servicio A exige 3.12)"; fi
else
  fail "python 3.12 no instalado"
fi
need uv opt 0.5 uv --version || true
need node req 20.0 node --version && {
  NV="$(ver node --version)"
  [[ "${NV%%.*}" -ge 22 ]] || warn "Node $NV: Node 20 está EOL desde 2026-04 (ver Q-B-5)"
}
need npm req 10.0 npm --version || true
need docker req 24.0 docker --version && {
  docker info >/dev/null 2>&1 && ok "docker daemon en marcha" || warn "docker daemon no responde (necesario para compose y Testcontainers)"
}
need kubectl $INFRA 1.30 kubectl version --client || true
need eksctl $INFRA 0.200 eksctl version || true
need terraform req 1.10 terraform version || true
need aws $INFRA 2.0 aws --version || true
need git req 2.30 git --version || true
need make opt 3.8 make --version || warn "sin make: usa 'bash scripts/py.sh scripts/<script>.py' (ver Makefile)"
need kubeconform opt 0.6 kubeconform -v || true
need gitleaks opt 8.0 gitleaks version || true
if have aws; then
  if ACC="$(aws sts get-caller-identity --query Account --output text --cli-connect-timeout 5 --cli-read-timeout 10 2>/dev/null)"; then
    ok "aws sts get-caller-identity → cuenta ****${ACC: -4}"
  else
    if [ "$MODE" = check ] || [ "$INFRA" = opt ]; then warn "aws sts get-caller-identity falló (sin credenciales o sin red)"; else fail "aws sts get-caller-identity falló"; fi
  fi
fi

# ─── 2. dependencias ─────────────────────────────────────────────────────────
hdr "2/5 Dependencias"
if [ "$MODE" = check ]; then
  [ -d .venv-tools ] && ok ".venv-tools presente" || warn ".venv-tools ausente: ejecuta ./init.sh"
  for d in services/service-b frontend; do
    [ -f "$d/package.json" ] && { [ -d "$d/node_modules" ] && ok "$d/node_modules" || warn "$d sin node_modules"; }
  done
  [ -f .env ] && ok ".env presente" || warn ".env ausente: cp .env.example .env"
else
  if [ -n "$PY" ]; then
    [ -d .venv-tools ] || "$PY" -m venv .venv-tools
    TOOLS_PY=".venv-tools/bin/python"; [ -x "$TOOLS_PY" ] || TOOLS_PY=".venv-tools/Scripts/python.exe"
    "$TOOLS_PY" -m pip install -q --disable-pip-version-check -r scripts/requirements-tools.txt \
      && ok "herramientas del harness (.venv-tools)" || fail "pip install scripts/requirements-tools.txt"
    if [ -d .git ] && "$TOOLS_PY" -m pre_commit --version >/dev/null 2>&1; then
      "$TOOLS_PY" -m pre_commit install --install-hooks -t pre-commit -t commit-msg >/dev/null 2>&1 \
        && ok "pre-commit instalado (pre-commit + commit-msg)" || warn "pre-commit install falló"
    fi
  fi
  if [ -f services/service-a/pyproject.toml ]; then
    if have uv; then (cd services/service-a && uv sync --frozen 2>/dev/null || uv sync) >/dev/null && ok "service-a: uv sync" || fail "service-a: uv sync"
    else fail "service-a requiere uv (pip install uv)"; fi
  else ok "service-a: sin pyproject.toml todavía (TASK-A-01)"; fi
  for d in services/service-b frontend; do
    if [ -f "$d/package.json" ]; then
      if [ -f "$d/package-lock.json" ]; then (cd "$d" && npm ci --no-audit --no-fund >/dev/null) && ok "$d: npm ci" || fail "$d: npm ci"
      else (cd "$d" && npm install --no-audit --no-fund >/dev/null) && ok "$d: npm install" || fail "$d: npm install"; fi
    else ok "$d: sin package.json todavía"; fi
  done
  if [ ! -f .env ]; then cp .env.example .env && ok ".env creado desde .env.example (valores locales)"; else ok ".env existente (no se toca)"; fi
fi

# ─── 3. docker compose ───────────────────────────────────────────────────────
hdr "3/5 docker compose"
if [ "$UP" = 1 ]; then
  SVCS="postgres mongo"
  [ -f services/service-a/Dockerfile ] && SVCS="$SVCS service-a"
  [ -f services/service-b/Dockerfile ] && SVCS="$SVCS service-b"
  [ -f frontend/Dockerfile ] && SVCS="$SVCS frontend"
  # shellcheck disable=SC2086
  docker compose up -d --build --wait $SVCS && ok "compose arriba: $SVCS" || fail "docker compose up"
else
  ok "omitido (usa --up para levantar el stack)"
fi

# ─── 4. smoke ────────────────────────────────────────────────────────────────
hdr "4/5 Smoke de salud"
probe() { # probe <nombre> <url>
  local code; code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$2" 2>/dev/null)"
  if [ "$code" = 200 ]; then ok "$1 $2 → 200"; else
    if [ "$UP" = 1 ]; then fail "$1 $2 → ${code:-sin respuesta}"; else warn "$1 $2 → ${code:-sin respuesta}"; fi
  fi
}
RUNNING="$(docker compose ps --services --status running 2>/dev/null || true)"
if [ -z "$RUNNING" ]; then
  ok "stack local no está en marcha: smoke omitido"
else
  echo "$RUNNING" | grep -qx service-a && probe "service-a" "http://localhost:${SERVICE_A_PORT:-8000}/health/ready"
  echo "$RUNNING" | grep -qx service-b && probe "service-b" "http://localhost:${SERVICE_B_PORT:-3000}/health/ready"
  echo "$RUNNING" | grep -qx frontend && {
    probe "frontend " "http://localhost:${FRONTEND_PORT:-8080}/health/ready"
    probe "proxy A  " "http://localhost:${FRONTEND_PORT:-8080}/api/a/health/ready"
    probe "proxy B  " "http://localhost:${FRONTEND_PORT:-8080}/api/b/health/ready"
  }
fi

# ─── 5. resumen ──────────────────────────────────────────────────────────────
hdr "5/5 Estado"
if [ -n "$PY" ]; then bash scripts/py.sh scripts/status.py --brief || warn "status.py falló"; fi

printf '\n'
if [ "$ERRORS" -gt 0 ]; then
  printf '\033[31minit: %d error(es), %d aviso(s)\033[0m\n' "$ERRORS" "$WARNINGS"
  [ "$MODE" = check ] && exit 0 || exit 1   # --check nunca bloquea el inicio de sesión
fi
printf '\033[32minit: OK\033[0m (%d aviso(s)). Flujo: /status → /implement <TASK-ID> → make verify\n' "$WARNINGS"
exit 0
