#!/usr/bin/env bash
# Renderiza deploy/eksctl/cluster.yaml con el ID de cuenta → .harness/cluster.rendered.yaml
#   --no-access-entries  omite accessEntries (para crear el clúster antes de que exista el rol IAM)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ACC="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
OUT="$ROOT/.harness/cluster.rendered.yaml"
mkdir -p "$ROOT/.harness"
sed "s/\${AWS_ACCOUNT_ID}/$ACC/g" "$ROOT/deploy/eksctl/cluster.yaml" > "$OUT"
if [[ "${1:-}" == "--no-access-entries" ]]; then
  # elimina el bloque accessEntries (hasta la línea 'addons:')
  awk '/^  accessEntries:/{skip=1} /^addons:/{skip=0; print ""} !skip' "$OUT" > "$OUT.tmp" && mv "$OUT.tmp" "$OUT"
fi
echo "$OUT"
