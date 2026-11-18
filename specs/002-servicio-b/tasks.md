# 002 · Servicio B — tareas

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md). Pruebas antes que implementación.

- [ ] **TASK-B-01** — Esqueleto del proyecto (tooling, sin lógica)
  - Tipo: scaffold
  - Depende de: —
  - REQ: —
  - Archivos: `services/service-b/package.json`, `services/service-b/package-lock.json`, `services/service-b/tsconfig.json`, `services/service-b/tsconfig.build.json`, `services/service-b/eslint.config.js`, `services/service-b/.prettierrc.json`, `services/service-b/.prettierignore`, `services/service-b/vitest.config.ts`, `services/service-b/.nvmrc`, `services/service-b/README.md`, `services/service-b/src/index.ts`, `services/service-b/tests/setup.ts`
  - Hecho cuando: `npm ci` instala; existen los scripts `lint`, `typecheck`, `test:unit`, `test:integration`, `test:contract`, `build`; `make verify` verde.

- [ ] **TASK-B-02** — Pruebas: config, logging, health
  - Tipo: test
  - Depende de: TASK-B-01
  - REQ: REQ-B-013, REQ-B-014, REQ-SYS-004, REQ-SYS-005
  - Archivos: `services/service-b/tests/unit/config.test.ts`, `services/service-b/tests/unit/logger.test.ts`, `services/service-b/tests/unit/health.test.ts`, `services/service-b/tests/integration/health-mongo.test.ts`, `services/service-b/tests/integration/mongo-container.ts`
  - Hecho cuando: pruebas escritas en rojo (`it.fails`); `make verify` verde.

- [ ] **TASK-B-03** — Implementación: config, logger, request-id, health, conexión Mongo
  - Tipo: impl
  - Depende de: TASK-B-02
  - REQ: REQ-B-013, REQ-B-014, REQ-SYS-004, REQ-SYS-005
  - Archivos: `services/service-b/src/main.ts`, `services/service-b/src/app.ts`, `services/service-b/src/config.ts`, `services/service-b/src/logger.ts`, `services/service-b/src/clock.ts`, `services/service-b/src/api/health.ts`, `services/service-b/src/repository/mongo.ts`, `services/service-b/src/index.ts`, `services/service-b/tests/unit/*.test.ts`, `services/service-b/tests/integration/health-mongo.test.ts`
  - Hecho cuando: pruebas de B-02 en verde (sin `it.fails`); `make verify` verde.

- [ ] **TASK-B-04** — Pruebas: repositorios e índices (integración)
  - Tipo: test
  - Depende de: TASK-B-03
  - REQ: REQ-B-015, REQ-B-006, REQ-B-001, REQ-B-002, REQ-B-003, REQ-B-004, REQ-B-005, REQ-B-008, REQ-B-009, REQ-B-010, REQ-B-011
  - Archivos: `services/service-b/tests/integration/indexes.test.ts`, `services/service-b/tests/integration/member-repository.test.ts`, `services/service-b/tests/integration/loan-repository.test.ts`
  - Hecho cuando: pruebas contra Mongo de Testcontainers escritas en rojo.

- [ ] **TASK-B-05** — Implementación: repositorios Mongo e índices
  - Tipo: impl
  - Depende de: TASK-B-04
  - REQ: REQ-B-015, REQ-B-006, REQ-B-001, REQ-B-002, REQ-B-003, REQ-B-004, REQ-B-005, REQ-B-008, REQ-B-009, REQ-B-010, REQ-B-011
  - Archivos: `services/service-b/src/repository/indexes.ts`, `services/service-b/src/repository/mongo-member-repository.ts`, `services/service-b/src/repository/mongo-loan-repository.ts`, `services/service-b/src/domain/ports.ts`, `services/service-b/src/main.ts`, `services/service-b/tests/integration/*.test.ts`
  - Hecho cuando: pruebas de B-04 en verde; `make verify` verde.

- [ ] **TASK-B-06** [P] — Pruebas: dominio de socios
  - Tipo: test
  - Depende de: TASK-B-01
  - REQ: REQ-B-001, REQ-B-007
  - Archivos: `services/service-b/tests/unit/member.test.ts`, `services/service-b/tests/unit/layers.test.ts`
  - Hecho cuando: pruebas en rojo (normalización de email, límites de longitud, teléfono).

- [ ] **TASK-B-07** — Implementación: dominio de socios
  - Tipo: impl
  - Depende de: TASK-B-06
  - REQ: REQ-B-001, REQ-B-007
  - Archivos: `services/service-b/src/domain/member.ts`, `services/service-b/src/domain/errors.ts`, `services/service-b/tests/unit/member.test.ts`, `services/service-b/tests/unit/layers.test.ts`
  - Hecho cuando: pruebas de B-06 en verde; `make verify` verde.

- [ ] **TASK-B-08** [P] — Pruebas: dominio de préstamos (reglas y estado derivado)
  - Tipo: test
  - Depende de: TASK-B-01
  - REQ: REQ-B-008, REQ-B-011, REQ-B-012
  - Archivos: `services/service-b/tests/unit/loan.test.ts`, `services/service-b/tests/unit/fake-clock.ts`
  - Hecho cuando: pruebas en rojo para cada regla 1–5 de REQ-B-008 y para overdue con reloj falso.

- [ ] **TASK-B-09** — Implementación: dominio de préstamos
  - Tipo: impl
  - Depende de: TASK-B-08, TASK-B-07
  - REQ: REQ-B-008, REQ-B-011, REQ-B-012
  - Archivos: `services/service-b/src/domain/loan.ts`, `services/service-b/src/domain/errors.ts`, `services/service-b/tests/unit/loan.test.ts`
  - Hecho cuando: pruebas de B-08 en verde; `make verify` verde.

- [ ] **TASK-B-10** — Pruebas: API de socios
  - Tipo: test
  - Depende de: TASK-B-05, TASK-B-07
  - REQ: REQ-B-001, REQ-B-002, REQ-B-003, REQ-B-004, REQ-B-005, REQ-B-006, REQ-B-007, REQ-SYS-006
  - Archivos: `services/service-b/tests/unit/members-api.test.ts`, `services/service-b/tests/unit/fakes.ts`
  - Hecho cuando: pruebas en rojo cubriendo todos los Dado/Cuando/Entonces de socios.

- [ ] **TASK-B-11** — Implementación: casos de uso y API de socios + problem+json
  - Tipo: impl
  - Depende de: TASK-B-10
  - REQ: REQ-B-001, REQ-B-002, REQ-B-003, REQ-B-004, REQ-B-005, REQ-B-006, REQ-B-007, REQ-SYS-006
  - Archivos: `services/service-b/src/domain/member-service.ts`, `services/service-b/src/api/members.ts`, `services/service-b/src/api/schemas.ts`, `services/service-b/src/api/errors.ts`, `services/service-b/src/app.ts`, `services/service-b/tests/unit/members-api.test.ts`
  - Hecho cuando: pruebas de B-10 en verde; `make verify` verde.

- [ ] **TASK-B-12** — Pruebas: API de préstamos
  - Tipo: test
  - Depende de: TASK-B-09, TASK-B-11
  - REQ: REQ-B-008, REQ-B-009, REQ-B-010, REQ-B-011, REQ-B-012
  - Archivos: `services/service-b/tests/unit/loans-api.test.ts`, `services/service-b/tests/unit/fakes.ts`
  - Hecho cuando: pruebas en rojo.

- [ ] **TASK-B-13** — Implementación: casos de uso y API de préstamos
  - Tipo: impl
  - Depende de: TASK-B-12
  - REQ: REQ-B-008, REQ-B-009, REQ-B-010, REQ-B-011, REQ-B-012
  - Archivos: `services/service-b/src/domain/loan-service.ts`, `services/service-b/src/api/loans.ts`, `services/service-b/src/api/schemas.ts`, `services/service-b/src/app.ts`, `services/service-b/tests/unit/loans-api.test.ts`
  - Hecho cuando: pruebas de B-12 en verde; cobertura ≥ 80 %; `make verify` verde.

- [ ] **TASK-B-14** — Pruebas de contrato contra openapi.yaml
  - Tipo: test
  - Depende de: TASK-B-13
  - REQ: REQ-B-001, REQ-B-002, REQ-B-003, REQ-B-004, REQ-B-005, REQ-B-008, REQ-B-009, REQ-B-010, REQ-B-011, REQ-B-013, REQ-B-014
  - Archivos: `services/service-b/tests/contract/openapi-contract.test.ts`, `services/service-b/tests/contract/validator.ts`
  - Hecho cuando: cada `operationId` del contrato se ejercita y valida (status, content-type, esquema); `make verify` verde.
