# Architecture Decision Records

Formato: MADR simplificado (ver [0000-plantilla.md](0000-plantilla.md)).
Estados: Propuesto → Aceptado → (Reemplazado por NNNN | Obsoleto). Un ADR aceptado no se edita: se reemplaza.

| # | Decisión | Estado |
|---|---|---|
| [0001](0001-monorepo.md) | Monorepo | Propuesto |
| [0002](0002-bd-por-servicio.md) | Base de datos por servicio | Propuesto |
| [0003](0003-bd-dentro-del-cluster.md) | Bases de datos dentro del clúster (StatefulSet + EBS gp3) | Propuesto |
| [0004](0004-front-con-proxy-nginx.md) | Frontend con proxy reverso Nginx (sin CORS) | Propuesto |
| [0005](0005-reparto-eksctl-terraform-kubectl.md) | Reparto eksctl / Terraform / kubectl | Propuesto |
| [0006](0006-oidc-github-actions.md) | OIDC para GitHub Actions | Propuesto |
| [0007](0007-http-con-url-del-lb.md) | Solo HTTP con la URL del LoadBalancer | Propuesto |
| [0008](0008-verificacion-incremental.md) | Verificación incremental: trazabilidad por alcance y TDD con xfail estricto | Propuesto |
