# 003 · Frontend — tareas

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md). Pruebas antes que implementación.

- [ ] **TASK-F-01** — Esqueleto Vite + tooling (sin pantallas)
  - Tipo: scaffold
  - Depende de: —
  - REQ: —
  - Archivos: `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/eslint.config.js`, `frontend/.prettierrc.json`, `frontend/vitest.config.ts`, `frontend/playwright.config.ts`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/vite-env.d.ts`, `frontend/tests/setup.ts`, `frontend/README.md`, `frontend/.nvmrc`
  - Hecho cuando: `npm ci` y `npm run build` funcionan; existen los scripts del plan; `make verify` verde.

- [ ] **TASK-F-02** — Pruebas: configuración Nginx (integración)
  - Tipo: test
  - Depende de: TASK-F-01
  - REQ: REQ-F-008, REQ-F-009, REQ-SYS-001
  - Archivos: `frontend/tests/nginx/nginx.test.ts`, `frontend/tests/nginx/stub-upstream.ts`
  - Hecho cuando: pruebas en rojo que levantan `nginx-unprivileged` con la plantilla montada y dos upstreams stub.

- [ ] **TASK-F-03** — Implementación: plantilla Nginx
  - Tipo: impl
  - Depende de: TASK-F-02
  - REQ: REQ-F-008, REQ-F-009, REQ-SYS-001
  - Archivos: `frontend/nginx/templates/default.conf.template`, `frontend/tests/nginx/nginx.test.ts`
  - Hecho cuando: pruebas de F-02 en verde; `make verify` verde.

- [ ] **TASK-F-04** — Pruebas: cliente HTTP y tipos de contrato
  - Tipo: test
  - Depende de: TASK-F-01
  - REQ: REQ-F-007, REQ-F-009
  - Archivos: `frontend/tests/unit/http.test.ts`, `frontend/tests/unit/api-clients.test.ts`, `frontend/tests/msw/handlers.ts`, `frontend/tests/msw/server.ts`
  - Hecho cuando: pruebas en rojo (parseo problem+json, errores de red, rutas relativas).

- [ ] **TASK-F-05** — Implementación: cliente HTTP, generación de tipos y clientes A/B
  - Tipo: impl
  - Depende de: TASK-F-04
  - REQ: REQ-F-007, REQ-F-009
  - Archivos: `frontend/src/api/**`, `frontend/package.json`, `frontend/tests/unit/http.test.ts`, `frontend/tests/unit/api-clients.test.ts`
  - Hecho cuando: pruebas de F-04 en verde; `npm run test:contract` verde; `make verify` verde.

- [ ] **TASK-F-06** — Pruebas: pantallas de libros
  - Tipo: test
  - Depende de: TASK-F-05
  - REQ: REQ-F-001, REQ-F-002, REQ-F-003
  - Archivos: `frontend/tests/unit/books-list.test.tsx`, `frontend/tests/unit/book-form.test.tsx`, `frontend/tests/unit/isbn.test.ts`, `frontend/tests/msw/handlers.ts`
  - Hecho cuando: pruebas en rojo para cada Dado/Cuando/Entonces de F-001…003.

- [ ] **TASK-F-07** — Implementación: pantallas de libros y componentes compartidos
  - Tipo: impl
  - Depende de: TASK-F-06
  - REQ: REQ-F-001, REQ-F-002, REQ-F-003
  - Archivos: `frontend/src/features/books/**`, `frontend/src/shared/**`, `frontend/src/routes.tsx`, `frontend/src/App.tsx`, `frontend/tests/unit/books-list.test.tsx`, `frontend/tests/unit/book-form.test.tsx`, `frontend/tests/unit/isbn.test.ts`
  - Hecho cuando: pruebas de F-06 en verde; `make verify` verde.

- [ ] **TASK-F-08** [P] — Pruebas: pantallas de socios
  - Tipo: test
  - Depende de: TASK-F-05
  - REQ: REQ-F-004, REQ-F-007
  - Archivos: `frontend/tests/unit/members.test.tsx`, `frontend/tests/msw/handlers.ts`
  - Hecho cuando: pruebas en rojo (incluye 409 al borrar y 503 con banner).

- [ ] **TASK-F-09** — Implementación: pantallas de socios
  - Tipo: impl
  - Depende de: TASK-F-08, TASK-F-07
  - REQ: REQ-F-004, REQ-F-007
  - Archivos: `frontend/src/features/members/**`, `frontend/src/shared/**`, `frontend/src/routes.tsx`, `frontend/tests/unit/members.test.tsx`
  - Hecho cuando: pruebas de F-08 en verde; `make verify` verde.

- [ ] **TASK-F-10** — Pruebas: préstamos (composición A+B)
  - Tipo: test
  - Depende de: TASK-F-09
  - REQ: REQ-F-005, REQ-F-006, REQ-F-007
  - Archivos: `frontend/tests/unit/loans.test.tsx`, `frontend/tests/unit/loan-rows.test.ts`, `frontend/tests/msw/handlers.ts`
  - Hecho cuando: pruebas en rojo (incluye libro borrado en A y A caído).

- [ ] **TASK-F-11** — Implementación: préstamos
  - Tipo: impl
  - Depende de: TASK-F-10
  - REQ: REQ-F-005, REQ-F-006, REQ-F-007
  - Archivos: `frontend/src/features/loans/**`, `frontend/src/shared/**`, `frontend/src/routes.tsx`, `frontend/tests/unit/loans.test.tsx`, `frontend/tests/unit/loan-rows.test.ts`
  - Hecho cuando: pruebas de F-10 en verde; cobertura ≥ 80 %; `make verify` verde.

- [ ] **TASK-F-12** — E2E Playwright + accesibilidad
  - Tipo: test
  - Depende de: TASK-F-11, TASK-A-12, TASK-B-13, TASK-P-02
  - REQ: REQ-F-001, REQ-F-002, REQ-F-003, REQ-F-004, REQ-F-005, REQ-F-006, REQ-F-010
  - Archivos: `frontend/e2e/books.spec.ts`, `frontend/e2e/members.spec.ts`, `frontend/e2e/loans.spec.ts`, `frontend/e2e/a11y.spec.ts`, `frontend/e2e/fixtures.ts`, `frontend/src/**`
  - Hecho cuando: `make e2e` verde contra docker compose (chromium y firefox); `make verify` verde.
