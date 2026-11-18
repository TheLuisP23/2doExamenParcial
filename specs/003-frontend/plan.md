# 003 · Frontend — plan técnico

## Stack
| Pieza | Elección |
|---|---|
| Build | Vite 6+ · React 19 · TypeScript strict |
| Rutas | React Router |
| Datos | TanStack Query (caché, reintentos, invalidación) |
| Formularios | react-hook-form + zod (reglas espejo del contrato) |
| Tipos de API | `openapi-typescript` → `src/api/generated/{a,b}.ts` desde los `openapi.yaml` |
| Cliente HTTP | `fetch` envuelto (`src/api/http.ts`) que parsea problem+json |
| Estilos | CSS Modules, sin librería de UI |
| Pruebas | Vitest + Testing Library + MSW (mocks HTTP), Playwright (+ `@axe-core/playwright`) |
| Servidor | `nginxinc/nginx-unprivileged` (puerto 8080, no-root), plantillas `envsubst` |

## Estructura
```
frontend/
├── package.json · vite.config.ts · tsconfig.json · eslint.config.js · vitest.config.ts · playwright.config.ts
├── Dockerfile               # build (node) → runtime (nginx-unprivileged)
├── nginx/
│   └── templates/default.conf.template   # envsubst: ${SERVICE_A_UPSTREAM}, ${SERVICE_B_UPSTREAM}
├── src/
│   ├── main.tsx · App.tsx · routes.tsx
│   ├── api/                 # http.ts (problem+json), books.ts (A), members.ts y loans.ts (B), generated/
│   ├── features/books/ · features/members/ · features/loans/   # páginas + hooks + formularios
│   └── shared/              # componentes UI, ErrorBanner, ConfirmDialog, Pagination
├── tests/
│   ├── unit/                # componentes y hooks con MSW
│   └── nginx/               # Nginx real (Testcontainers) con upstreams stub
└── e2e/                     # Playwright contra docker compose (stack completo)
```
Capas: `features → api → http`. Las features no llaman `fetch` directamente (regla ESLint).
La composición A+B vive solo en `features/loans/` (hooks `useLoanRows` que combinan socio + libro).

## Scripts npm (contrato con `make verify`)
`lint`, `typecheck`, `test:unit` (vitest + coverage ≥ 80 %), `test:integration` (tests/nginx),
`test:contract` (comprueba que `src/api/generated` coincide con los `openapi.yaml`: `gen:api` + `git diff --exit-code`),
`e2e` (Playwright, no forma parte de `make verify`; `make e2e`), `build`.

## Estrategia de pruebas
| Nivel | Qué | Dónde |
|---|---|---|
| Unitarias | componentes, validación zod (ISBN), hooks de datos, parser problem+json, composición de filas de préstamo | `tests/unit` |
| Integración | config Nginx real: fallback SPA, strip de prefijo, health, cabeceras, X-Request-ID | `tests/nginx` (Testcontainers + upstreams stub) |
| Contrato | tipos generados sincronizados con contratos; MSW handlers tipados con esos tipos | `test:contract` |
| E2E | flujos HU-F-01…05 + axe, stack docker compose | `e2e/*.spec.ts` |

Trazabilidad: títulos de test con `[REQ-F-00X]`. TDD en rojo: `it.fails` (Vitest) / `test.fail()` (Playwright).
