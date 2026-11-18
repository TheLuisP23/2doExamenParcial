#!/usr/bin/env bash
# Sustituye SOLO ${ECR_REGISTRY} e ${IMAGE_TAG} en deploy/k8s/apps y escribe el resultado en stdout.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${ECR_REGISTRY:?define ECR_REGISTRY}" "${IMAGE_TAG:?define IMAGE_TAG}"
for f in "$ROOT"/deploy/k8s/apps/*.yaml; do
  sed -e "s#\${ECR_REGISTRY}#$ECR_REGISTRY#g" -e "s#\${IMAGE_TAG}#$IMAGE_TAG#g" "$f"
  echo "---"
done
