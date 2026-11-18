# Frontend — SPA del bibliotecario

React · Vite · TypeScript, servido por Nginx (`nginx-unprivileged`, puerto `8080`) con proxy reverso
`/api/a` → servicio A y `/api/b` → servicio B (sin CORS).

> **Estado: solo esqueleto.** El código se crea a partir de `TASK-F-01`
> ([specs/003-frontend/tasks.md](../specs/003-frontend/tasks.md)).

- Spec: [specs/003-frontend/spec.md](../specs/003-frontend/spec.md) · Plan: [plan.md](../specs/003-frontend/plan.md)
- Contratos consumidos: [A](../specs/001-servicio-a/contracts/openapi.yaml), [B](../specs/002-servicio-b/contracts/openapi.yaml)

Estructura prevista: `src/{api,features,shared}`, `nginx/templates/`, `tests/{unit,nginx}`, `e2e/`.
