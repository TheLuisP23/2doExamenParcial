#!/usr/bin/env bash
# Crea (idempotente) el bucket S3 del estado de Terraform y genera deploy/terraform/backend.hcl (no versionado).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGION="${AWS_REGION:-us-east-1}"
ACC="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="biblioteca-tfstate-$ACC"
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" >/dev/null
fi
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$BUCKET" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
printf 'bucket = "%s"\nkey    = "biblioteca/terraform.tfstate"\nregion = "%s"\n' "$BUCKET" "$REGION" > "$ROOT/.harness/backend.hcl"
echo "backend listo: s3://$BUCKET"
