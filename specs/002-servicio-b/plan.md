# 002 · Servicio B — plan técnico

## Stack
| Pieza | Elección | Motivo |
|---|---|---|
| Runtime | Node.js **24 LTS** (Q-B-5 resuelta) | soporte de seguridad |
| Lenguaje | TypeScript 5.x, `strict: true`, ESM | NFR-B-002 |
| Web | Express 5 | requisito |
| Validación | `zod` (esquemas `.strict()`), errores → problem+json | REQ-B-007 |
| Driver | `mongodb` oficial (sin ODM) | control explícito de índices y consultas |
| Config | `zod` sobre `process.env` (prefijo `SERVICE_B_`), falla rápido | REQ-SYS-005 |
| Logs | `pino` + `pino-http` (JSON) con `request_id` | REQ-SYS-004 |
| Lint/format | ESLint (typescript-eslint) + Prettier | — |
| Pruebas | Vitest + `@vitest/coverage-v8`, `supertest`, `@testcontainers/mongodb`, validación de contrato con `@apidevtools/swagger-parser` + `ajv` | ver estrategia |
| Fechas | `Date` en UTC; reloj inyectable (`Clock`) para pruebas deterministas | REQ-B-008, B-012 |

## Estructura y capas
```
services/service-b/
├── package.json · package-lock.json · tsconfig.json · eslint.config.js · vitest.config.ts · Dockerfile · README.md
├── src/
│   ├── main.ts              # arranque: config → mongo → índices → servidor
│   ├── app.ts               # createApp(deps): Express sin efectos secundarios (testeable)
│   ├── config.ts · logger.ts · clock.ts
│   ├── api/                 # CAPA API: routers, esquemas zod, mapeo DTO, problem+json
│   │   ├── health.ts · members.ts · loans.ts · errors.ts · schemas.ts
│   ├── domain/              # CAPA DOMINIO: entidades, reglas, casos de uso, puertos
│   │   ├── member.ts · loan.ts · errors.ts · ports.ts
│   │   └── member-service.ts · loan-service.ts
│   └── repository/          # CAPA REPOSITORIO: adaptadores MongoDB
│       ├── mongo.ts · indexes.ts · mongo-member-repository.ts · mongo-loan-repository.ts
└── tests/
    ├── unit/                # dominio + API con repos en memoria
    ├── integration/         # repos + índices + app con MongoDB (Testcontainers)
    └── contract/            # respuestas reales validadas contra openapi.yaml
```
Reglas de dependencia: `api → domain ← repository`; `domain` no importa `express` ni `mongodb`
(regla `no-restricted-imports` de ESLint + prueba de arquitectura).

## Configuración (variables de entorno)
| Variable | Obligatoria | Default | Uso |
|---|---|---|---|
| `SERVICE_B_MONGO_URI` | sí | — | cadena de conexión |
| `SERVICE_B_MONGO_DB` | no | `members` | nombre de BD |
| `SERVICE_B_PORT` | no | `3000` | puerto HTTP |
| `SERVICE_B_LOG_LEVEL` | no | `info` | nivel pino |
| `SERVICE_B_MAX_ACTIVE_LOANS` | no | `3` | REQ-B-008 |
| `SERVICE_B_DEFAULT_LOAN_DAYS` | no | `14` | REQ-B-008 |
| `SERVICE_B_READY_TIMEOUT_MS` | no | `2000` | REQ-B-014 |

## Scripts npm (contrato con `make verify`)
| Script | Comando |
|---|---|
| `lint` | `eslint . && prettier --check .` |
| `typecheck` | `tsc --noEmit` |
| `test:unit` | `vitest run tests/unit --coverage` (umbral 80 %) |
| `test:integration` | `vitest run tests/integration` |
| `test:contract` | `vitest run tests/contract` |
| `build` / `start` | `tsc -p tsconfig.build.json` / `node dist/main.js` |

## Estrategia de pruebas
| Nivel | Herramienta | Alcance |
|---|---|---|
| Unitarias | Vitest | reglas de préstamo (límite, elegibilidad, fechas con `Clock` falso), normalización de email, API con repos en memoria |
| Integración | Vitest + Testcontainers `mongo:7` | repositorios, índices (unicidad, índice parcial), readiness real |
| Contrato | Vitest + supertest + ajv | cada operación del `openapi.yaml` se ejercita y su respuesta (status + cuerpo + content-type) se valida contra el esquema |
| E2E | Playwright (`frontend/e2e`) | flujos de UI de socios y préstamos |
| Smoke | `tests/smoke` | `/api/b/health/ready` en EKS |

Trazabilidad: el título de cada `it/test` contiene `[REQ-B-00X]`. Las pruebas de TDD en rojo se
escriben con `it.fails(...)` y la tarea de implementación las convierte en `it(...)`.
