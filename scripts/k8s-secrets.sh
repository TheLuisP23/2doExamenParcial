#!/usr/bin/env bash
# REQ-P-012 — crea los Secrets de BD en el clúster con contraseñas aleatorias. Idempotente: no sobrescribe.
set -euo pipefail
NS=biblioteca
for s in postgres-credentials mongo-credentials; do
  if kubectl -n "$NS" get secret "$s" >/dev/null 2>&1; then
    echo "· $s ya existe (no se modifica)"
  else
    kubectl -n "$NS" create secret generic "$s" --from-literal=password="$(openssl rand -hex 24)" >/dev/null
    echo "✓ $s creado"
  fi
done
