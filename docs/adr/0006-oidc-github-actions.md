# 0006 — OIDC para GitHub Actions

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: constitución VI.3, REQ-P-005, REQ-P-014

## Contexto
El CD necesita publicar en ECR y desplegar en EKS. Guardar access keys de IAM en GitHub crea
credenciales de larga duración que pueden filtrarse.

## Decisión
Proveedor OIDC de IAM para `token.actions.githubusercontent.com` y rol `biblioteca-github-actions`,
asumible solo por `repo:<owner>/<repo>:ref:refs/heads/main` con `aud = sts.amazonaws.com`.
Permisos mínimos: push a los 3 repos ECR y `eks:DescribeCluster` sobre el clúster. La autorización
dentro del clúster se da con un *access entry* (`AmazonEKSEditPolicy` limitada al namespace `biblioteca`).

## Alternativas consideradas
- **Access keys en GitHub Secrets**: prohibido por la constitución.
- **`AmazonEKSClusterAdminPolicy`** para CI: más simple, pero excesivo.

## Consecuencias
- (+) Credenciales efímeras (≈1 h), revocables cambiando la trust policy.
- (−) CI no puede crear recursos cluster-scoped (StorageClass, Namespace) → los aplica el operador en el bootstrap.
- (−) La trust policy depende de `owner/repo` (Q-P-1).
