# deploy/k8s

Manifiestos YAML planos (sin Helm ni Kustomize), TASK-P-08. Estructura prevista:
`bootstrap/` (namespace + StorageClass, operador), `postgres/`, `mongo/`, `service-a/`, `service-b/`,
`frontend/` (Service LoadBalancer 80→8080), `policies/`. Validación: kubeconform `-strict` en `make verify`.
Los Secrets reales **nunca** se versionan: solo `*.example.yaml`.
