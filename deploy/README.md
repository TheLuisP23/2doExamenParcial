# deploy/

| Carpeta | Herramienta | Contenido (se crea en) |
|---|---|---|
| `terraform/` | Terraform | ECR ×3, OIDC de GitHub, rol IAM de CI, backend S3 (TASK-P-04) |
| `eksctl/` | eksctl | `cluster.yaml` — VPC, EKS 1.36, 2×t3.medium, addons, access entry (TASK-P-06) |
| `k8s/` | kubectl | manifiestos YAML planos: bootstrap, BDs, apps, políticas (TASK-P-08) |

Orden de aprovisionamiento: **terraform → eksctl → kubectl** (inverso para destruir).
Detalles: [specs/004-plataforma/plan.md](../specs/004-plataforma/plan.md) ·
[ADR-0005](../docs/adr/0005-reparto-eksctl-terraform-kubectl.md).

Ningún comando que cree o destruya recursos se ejecuta sin confirmación humana.
