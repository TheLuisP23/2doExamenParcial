# Servicio B — Socios y préstamos

Node.js (22 LTS, pendiente Q-B-5) · TypeScript · Express · MongoDB 7 · puerto `3000`.

> **Estado: solo esqueleto.** El código se crea a partir de `TASK-B-01`
> ([specs/002-servicio-b/tasks.md](../../specs/002-servicio-b/tasks.md)).

- Spec: [specs/002-servicio-b/spec.md](../../specs/002-servicio-b/spec.md)
- Contrato: [specs/002-servicio-b/contracts/openapi.yaml](../../specs/002-servicio-b/contracts/openapi.yaml)
- Modelo de datos: [data-model.md](../../specs/002-servicio-b/data-model.md) · Plan: [plan.md](../../specs/002-servicio-b/plan.md)

Estructura prevista: `src/{api,domain,repository}`, `tests/{unit,integration,contract}`.
Scripts npm (contrato con `make verify`): `lint`, `typecheck`, `test:unit`, `test:integration`, `test:contract`, `build`.
Este servicio **no** llama al servicio A: `book_id` es un identificador opaco.
