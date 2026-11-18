# 004 · Plataforma — contenedores, AWS, Kubernetes y CI/CD

- **Estado**: Borrador para revisión · **Versión**: 0.1.0 · **Fecha**: 2026-11-17
- **Región**: `us-east-1` · **Clúster**: `biblioteca-eks` · **Namespace**: `biblioteca`
- **Plan**: [plan.md](plan.md) · **Tareas**: [tasks.md](tasks.md) · ADRs: [0003](../../docs/adr/0003-bd-dentro-del-cluster.md), [0005](../../docs/adr/0005-reparto-eksctl-terraform-kubectl.md), [0006](../../docs/adr/0006-oidc-github-actions.md), [0007](../../docs/adr/0007-http-con-url-del-lb.md)

## Propósito
Empaquetar los tres componentes como imágenes, aprovisionar AWS (ECR, IAM/OIDC, EKS), desplegar
con manifiestos YAML planos y automatizar build/deploy con GitHub Actions sin credenciales estáticas.

## Historias de usuario
- **HU-P-01 (P1)** — Como desarrollador quiero levantar todo en local con un comando.
- **HU-P-02 (P1)** — Como operador quiero crear y destruir toda la infraestructura de forma reproducible y en orden.
- **HU-P-03 (P1)** — Como equipo quiero que cada push a `main` construya, publique y despliegue automáticamente.
- **HU-P-04 (P1)** — Como evaluador quiero acceder a la app por la URL pública del LoadBalancer.
- **HU-P-05 (P2)** — Como operador quiero que cada BD solo sea alcanzable por su servicio dentro del clúster.

## Requisitos — contenedores y local

### REQ-P-001 — Imágenes Docker (P1)
Un `Dockerfile` por componente (`services/service-a`, `services/service-b`, `frontend`): multi-stage,
base con versión fijada (tag + digest recomendado), usuario **no-root** (UID ≥ 10000), sin herramientas
de build en la etapa final, sin secretos ni `.env` (`.dockerignore`), `EXPOSE` del puerto del plan.
- **Dado** cada Dockerfile, **cuando** se analiza, **entonces** la última etapa tiene `USER` numérico ≠ 0 y ningún `FROM` usa `latest`.
- **Dado** la imagen construida, **cuando** se ejecuta `id -u`, **entonces** ≠ 0.

### REQ-P-002 — docker compose local (P1)
`docker-compose.yml` levanta `postgres`, `mongo`, `service-a`, `service-b`, `frontend` con healthchecks,
`depends_on: condition: service_healthy`, volúmenes nombrados y variables desde `.env`. Solo el front
publica puerto al host (`8080`); A/B publican `8000`/`3000` solo para depuración local.
- **Dado** `./init.sh --up`, **entonces** todos los servicios quedan `healthy` y `http://localhost:8080/api/a/health/ready` → `200`.

## Requisitos — AWS (Terraform)

### REQ-P-003 — Estado remoto (P1)
Backend `s3` con `use_lockfile = true` (bloqueo nativo S3, sin DynamoDB), cifrado y versionado del bucket,
acceso público bloqueado. Nombre del bucket y clave por `-backend-config` (no en el repo).
- **Dado** `deploy/terraform`, **entonces** el bloque `backend "s3"` declara `use_lockfile = true` y `encrypt = true`.

### REQ-P-004 — Repositorios ECR (P1)
Tres repos: `biblioteca/service-a`, `biblioteca/service-b`, `biblioteca/frontend`; `image_tag_mutability = IMMUTABLE`,
`scan_on_push = true`, cifrado AES256, política de ciclo de vida que conserva las últimas 10 imágenes; `force_delete = true` (entorno académico).

### REQ-P-005 — OIDC de GitHub y rol IAM de mínimo privilegio (P1)
Proveedor OIDC `token.actions.githubusercontent.com` (audiencia `sts.amazonaws.com`) y rol
`biblioteca-github-actions` cuya *trust policy* exige `aud = sts.amazonaws.com` y
`sub = repo:<owner>/<repo>:ref:refs/heads/main` (y opcionalmente `environment:production`).
Permisos: `ecr:GetAuthorizationToken` (`*`); `ecr:BatchCheckLayerAvailability`, `ecr:InitiateLayerUpload`,
`ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`, `ecr:PutImage`, `ecr:BatchGetImage`,
`ecr:DescribeImages` **solo** sobre los 3 repos; `eks:DescribeCluster` **solo** sobre el ARN del clúster.
- **Dado** el plan de Terraform, **entonces** ninguna sentencia del rol usa `Action: "*"` ni `Resource: "*"` salvo `ecr:GetAuthorizationToken`.
- **Dado** un workflow de otra rama o repo, **cuando** intenta asumir el rol, **entonces** STS lo rechaza.

## Requisitos — clúster (eksctl)

### REQ-P-006 — ClusterConfig versionado (P1)
`deploy/eksctl/cluster.yaml` (`eksctl.io/v1alpha5`): nombre `biblioteca-eks`, región `us-east-1`,
Kubernetes **1.37** (vigente en EKS; eksctl 0.231 soporta 1.31–1.37), VPC gestionada por eksctl
(CIDR `10.10.0.0/16`, 2 AZ, NAT gateway único), `iam.withOIDC: true`, *managed node group*
`ng-default` de **2 × t3.medium** (min 2, max 3, disco gp3 30 GiB, subredes privadas), addons
`vpc-cni` (con `enableNetworkPolicy`), `coredns`, `kube-proxy`, `aws-ebs-csi-driver` (IRSA con la
política gestionada del driver), `accessConfig.authenticationMode: API` y *access entry* para el rol de
GitHub Actions con `AmazonEKSEditPolicy` limitada al namespace `biblioteca`.
- **Dado** el archivo, **cuando** `eksctl create cluster -f <render> --dry-run`, **entonces** termina sin error.
- **Dado** el archivo, **entonces** no contiene el ID de cuenta literal (se inyecta al renderizar).

## Requisitos — Kubernetes (kubectl, YAML planos)

### REQ-P-007 — StorageClass gp3 (P1)
`gp3` con provisioner `ebs.csi.aws.com`, `type: gp3`, `encrypted: "true"`, `volumeBindingMode: WaitForFirstConsumer`, `reclaimPolicy: Delete`, `allowVolumeExpansion: true`.

### REQ-P-008 — PostgreSQL como StatefulSet (P1)
`postgres:16-alpine` (versión menor fijada), 1 réplica, `volumeClaimTemplates` 10 GiB `gp3`, Service headless,
credenciales desde Secret, probes (`pg_isready`), requests/limits, `PGDATA` en subdirectorio del volumen.

### REQ-P-009 — MongoDB como StatefulSet (P1)
`mongo:7` (versión menor fijada), 1 réplica standalone, PVC 10 GiB `gp3`, Service headless, usuario root y usuario
de aplicación (`readWrite` en `members`) creados por script de init desde Secret, probes (`mongosh --eval ping`), requests/limits.

### REQ-P-010 — Deployments de A, B y front (P1)
2 réplicas cada uno; `readinessProbe` → `/health/ready`, `livenessProbe` → `/health/live`, `startupProbe`;
requests/limits; `securityContext` (`runAsNonRoot`, `readOnlyRootFilesystem` con `emptyDir` para `/tmp`,
`allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault`);
configuración por ConfigMap/Secret; imagen `${ECR_REGISTRY}/biblioteca/<app>:${IMAGE_TAG}`.
- **Dado** cualquier contenedor de cualquier manifiesto, **entonces** declara `resources.requests` y `resources.limits` de CPU y memoria.

### REQ-P-011 — Services (P1)
`ClusterIP` para A (`8000`), B (`3000`), y headless para BDs; **solo** `frontend` es `type: LoadBalancer`,
`port: 80 → targetPort: 8080`, protocolo TCP/HTTP, sin TLS. La URL pública es el DNS del ELB.
- **Dado** los manifiestos, **entonces** exactamente un Service es `LoadBalancer` y es el del front.

### REQ-P-012 — Configuración y secretos (P1)
ConfigMaps para configuración no sensible. Ningún `Secret` con datos reales en el repo: solo
`*.example.yaml` con valores `REPLACE_ME`. `scripts/k8s-secrets.sh` crea los Secrets en el clúster
(contraseñas aleatorias, idempotente: no sobrescribe si ya existen).
- **Dado** el repo, **entonces** no hay `kind: Secret` con `data`/`stringData` reales fuera de `*.example.yaml`.

### REQ-P-017 — Namespace y etiquetas (P1)
Todo recurso namespaced vive en `biblioteca` y lleva `app.kubernetes.io/name`, `app.kubernetes.io/part-of: biblioteca`, `app.kubernetes.io/component`.

### REQ-P-018 — NetworkPolicies (P2)
*Default deny* de ingreso en el namespace; permitir: LB → front:8080; front → A:8000 y B:3000;
A → postgres:5432; B → mongo:27017; DNS a kube-system.
- **Dado** las políticas, **entonces** postgres solo admite ingreso desde pods `service-a` y mongo solo desde `service-b`.

## Requisitos — CI/CD (GitHub Actions)

### REQ-P-013 — CI en pull requests (P1)
`.github/workflows/ci.yml` en `pull_request` y `push`: instala toolchain y ejecuta `make verify`
(incluye kubeconform, `terraform validate`, trazabilidad) y gitleaks. Sin credenciales AWS.
`permissions: contents: read`.

### REQ-P-014 — CD en `main` (P1)
`.github/workflows/cd.yml` en `push` a `main` (y `workflow_dispatch`): `permissions: id-token: write, contents: read`;
`aws-actions/configure-aws-credentials` con `role-to-assume` (variable de repo, no secreto) — **sin access keys**;
build y push de las 3 imágenes con tag = `github.sha`; `aws eks update-kubeconfig`; render de manifiestos
(`envsubst` solo de `ECR_REGISTRY` e `IMAGE_TAG`); `kubectl apply -n biblioteca`; `kubectl rollout status`;
smoke tests contra el DNS del LB. Acciones de terceros fijadas por SHA. `concurrency` para no solapar despliegues.
- **Dado** el workflow, **entonces** no referencia `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY`.

### REQ-P-015 — Smoke tests post-deploy (P1)
`tests/smoke` (pytest, `SMOKE_BASE_URL`): `GET /` → 200 HTML; `/api/a/health/ready` y `/api/b/health/ready` → 200;
`/health/ready` del front → 200; reintentos con espera hasta 5 min (propagación DNS del ELB).

### REQ-P-016 — Orden de aprovisionamiento y destrucción (P1)
`make infra-up`: backend S3 → `terraform apply` (ECR + OIDC + rol) → render + `eksctl create cluster` (con access entry
del rol) → `kubectl apply` de bootstrap (namespace, StorageClass) → Secrets → primer despliegue.
`make infra-down` (inverso): borrar Service LoadBalancer y namespace (libera ELB y EBS) → `eksctl delete cluster --wait` → `terraform destroy`.
Cada paso requiere confirmación humana (ver `.claude/settings.json`).
- **Dado** `infra-down`, **entonces** el Service LoadBalancer se borra **antes** que el clúster (si no, el ELB y sus SG quedan huérfanos e impiden borrar la VPC).

## Requisitos no funcionales
| ID | Requisito |
|---|---|
| NFR-P-001 | Coste: el clúster se destruye al terminar cada sesión de pruebas (`make infra-down`); tags `Project=biblioteca` en todo recurso |
| NFR-P-002 | Despliegue reproducible desde cero en < 30 min |
| NFR-P-003 | Manifiestos válidos para la versión de K8s del clúster (kubeconform `-kubernetes-version`) |

## Fuera de alcance
Helm, Kustomize, Argo CD/Flux, Ingress/AWS Load Balancer Controller, TLS/ACM, Route 53, WAF, Karpenter/autoscaling
de nodos, HPA, RDS/DocumentDB, backups de BD, multi-entorno (staging/prod), observabilidad gestionada (CloudWatch Container Insights),
External Secrets/Secrets Manager, firmado de imágenes.

## Preguntas abiertas (resueltas 2026-11-17)
- Q-P-1: repositorio **`TheLuisP23/2doExamenParcial`** (trust policy: `repo:TheLuisP23/2doExamenParcial:ref:refs/heads/main`).
- Q-P-2: bucket de estado `biblioteca-tfstate-<account-id>` (lo crea `scripts/tf-backend-bootstrap.sh`).
- Q-P-3: Kubernetes **1.37** (coincide con el kubectl 1.37 instalado; eksctl 0.231 lo soporta).
- Q-P-4: **Classic LB** por defecto (sin anotaciones; lo más rápido).
- Q-P-5: CD **automático** en push a `main`, sin aprobación manual.
- Q-P-6: el CD construye siempre las 3 imágenes.
- Q-P-7: AWS CLI 2.17.57 suficiente para el alcance (no se actualiza).
- Desviación de orden aceptada por tiempo: el clúster se crea primero sin access entry y la access entry del rol
  de GitHub se añade tras `terraform apply` (`eksctl create accessentry`).
