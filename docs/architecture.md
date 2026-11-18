# Arquitectura (modelo C4)

> Fuente: [specs/000-sistema](../specs/000-sistema/spec.md) y [specs/004-plataforma](../specs/004-plataforma/spec.md).
> Decisiones: [docs/adr](adr/README.md).

## Nivel 1 — Contexto
```mermaid
C4Context
  title Biblioteca — contexto del sistema
  Person(lib, "Bibliotecario", "Gestiona catálogo, socios y préstamos desde el navegador")
  Person(ops, "Operador de plataforma", "Aprovisiona AWS con Terraform/eksctl/kubectl")
  System(sys, "Sistema Biblioteca", "SPA + servicio de libros + servicio de socios/préstamos")
  System_Ext(gh, "GitHub Actions", "CI/CD; se autentica en AWS por OIDC")
  System_Ext(aws, "AWS", "EKS, ECR, IAM, ELB, EBS, S3 (estado Terraform)")
  Rel(lib, sys, "Usa", "HTTP :80 (DNS del LoadBalancer)")
  Rel(ops, aws, "Aprovisiona", "AWS CLI / eksctl / terraform / kubectl")
  Rel(gh, aws, "Publica imágenes y despliega", "OIDC → STS → ECR / EKS")
  Rel(sys, aws, "Se ejecuta en")
```

## Nivel 2 — Contenedores
```mermaid
C4Container
  title Biblioteca — contenedores
  Person(lib, "Bibliotecario")
  System_Boundary(b, "Clúster EKS · namespace biblioteca") {
    Container(fe, "Frontend", "React + Vite servido por Nginx :8080", "SPA; proxy /api/a → A, /api/b → B; sin CORS")
    Container(sa, "Servicio A — Libros", "Python 3.12 · FastAPI :8000", "CRUD y búsqueda del catálogo")
    ContainerDb(pg, "PostgreSQL 16", "StatefulSet + PVC gp3", "BD exclusiva de A")
    Container(sb, "Servicio B — Socios y préstamos", "Node · TypeScript · Express :3000", "Socios, préstamos, devoluciones")
    ContainerDb(mg, "MongoDB 7", "StatefulSet + PVC gp3", "BD exclusiva de B")
  }
  Rel(lib, fe, "HTTP", ":80 → LB → :8080")
  Rel(fe, sa, "Proxy /api/a/*", "HTTP, prefijo eliminado")
  Rel(fe, sb, "Proxy /api/b/*", "HTTP, prefijo eliminado")
  Rel(sa, pg, "SQL", "psycopg :5432")
  Rel(sb, mg, "Wire protocol", "mongodb :27017")
```
**Invariante**: no existe ninguna flecha A ↔ B ni A → MongoDB ni B → PostgreSQL (REQ-SYS-002,
NetworkPolicies REQ-P-018). La composición (préstamo + título del libro) ocurre en el navegador.

## Nivel 3 — Componentes (ambos servicios siguen la misma forma)
```mermaid
flowchart LR
  subgraph svc["Servicio (A o B)"]
    api["api/<br/>routers · esquemas HTTP · problem+json"] --> dom["domain/<br/>entidades · reglas · casos de uso · puertos"]
    repo["repository/<br/>adaptador SQLAlchemy | MongoDB"] -. implementa puerto .-> dom
    cfg["config · logging · health"] --> api
  end
  repo --> db[(BD propia)]
```
`domain` no depende de frameworks (comprobado por pruebas de capas).

## Despliegue
```mermaid
flowchart TB
  user((Navegador)) -->|HTTP :80| elb[ELB de AWS<br/>creado por Service type LoadBalancer]
  subgraph vpc["VPC 10.10.0.0/16 (eksctl) · us-east-1a / us-east-1b"]
    elb --> fe1 & fe2
    subgraph ng["Managed node group · 2 × t3.medium (subredes privadas)"]
      fe1[frontend pod] & fe2[frontend pod]
      a1[service-a pod] & a2[service-a pod]
      b1[service-b pod] & b2[service-b pod]
      pg[(postgres-0)]
      mg[(mongo-0)]
    end
    pg --- ebs1[(EBS gp3 10Gi)]
    mg --- ebs2[(EBS gp3 10Gi)]
  end
  gh[GitHub Actions] -->|OIDC AssumeRoleWithWebIdentity| iam[Rol IAM biblioteca-github-actions]
  iam -->|push| ecr[(ECR ×3)]
  iam -->|eks:DescribeCluster + access entry Edit ns biblioteca| vpc
  ng -->|pull| ecr
```

## Flujo de una petición típica: "registrar préstamo"
```mermaid
sequenceDiagram
  participant U as Navegador (SPA)
  participant N as Nginx
  participant A as Servicio A
  participant B as Servicio B
  U->>N: GET /api/b/members?status=active&q=ana
  N->>B: GET /members?status=active&q=ana
  B-->>U: socios
  U->>N: GET /api/a/books?q=borges
  N->>A: GET /books?q=borges
  A-->>U: libros
  U->>N: POST /api/b/loans {member_id, book_id}
  N->>B: POST /loans (book_id opaco, sin llamar a A)
  B-->>U: 201 Loan
```
