# deploy/terraform

Recursos AWS fuera del clúster (TASK-P-04): ECR ×3, proveedor OIDC de GitHub, rol IAM de CI/CD.
Estado remoto en S3 con `use_lockfile = true`. Requisitos: REQ-P-003, REQ-P-004, REQ-P-005
([spec](../../specs/004-plataforma/spec.md)). `terraform apply/destroy` requieren confirmación humana.
