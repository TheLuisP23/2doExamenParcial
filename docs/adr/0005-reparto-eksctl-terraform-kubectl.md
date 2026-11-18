# 0005 — Reparto eksctl / Terraform / kubectl

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: REQ-P-003…REQ-P-016

## Contexto
Hay que crear recursos AWS fuera del clúster, el clúster en sí y los recursos de Kubernetes. Cada
herramienta es mejor en una capa; mezclarlas sin reglas produce dos dueños para el mismo recurso.

## Decisión
| Capa | Herramienta | Recursos |
|---|---|---|
| AWS fuera del clúster | Terraform (estado S3 + `use_lockfile`) | ECR ×3, OIDC de GitHub, rol IAM de CI |
| Clúster | eksctl (`deploy/eksctl/cluster.yaml`) | VPC, EKS, managed node group, addons, access entries |
| Dentro del clúster | kubectl + YAML planos | namespace, StorageClass, StatefulSets, Deployments, Services, NetworkPolicies, ConfigMaps |

Orden: Terraform → eksctl → kubectl (el access entry necesita que el rol exista; ver el plan de 004).
Cada recurso tiene un único dueño; nadie modifica a mano lo que gestiona otra herramienta.

## Alternativas consideradas
- **Todo en Terraform** (módulo `terraform-aws-modules/eks`): un solo estado, pero el enunciado pide eksctl.
- **Helm/Kustomize**: excluidos por el enunciado.

## Consecuencias
- (+) Cada herramienta en su punto fuerte; `cluster.yaml` legible y versionado.
- (−) Tres "estados" (S3, CloudFormation de eksctl, git) → `make infra-up/down` los orquesta en orden.
- (−) Sin plantillas, los manifiestos repiten etiquetas; el único render es `envsubst` de registro y tag.
