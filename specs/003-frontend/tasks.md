# 003 · Frontend — tareas (modo vía rápida)

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md).
> **2026-11-17 — vía rápida**: las 12 tareas originales se consolidan (desglose original en el commit `24a9bdf`).

- [x] **TASK-F-01** — Frontend completo: SPA, cliente HTTP, pantallas, Nginx y Dockerfile
  - Tipo: impl
  - Depende de: —
  - REQ: REQ-F-001, REQ-F-002, REQ-F-003, REQ-F-004, REQ-F-005, REQ-F-006, REQ-F-007, REQ-F-008, REQ-F-009, REQ-SYS-001
  - Archivos: `frontend/**`
  - Hecho cuando: lint, typecheck y pruebas unitarias en verde; imagen construye y sirve la SPA con proxy; `make verify` verde.

- [ ] **TASK-F-02** — E2E Playwright + accesibilidad (opcional si queda tiempo)
  - Tipo: test
  - Depende de: TASK-F-01
  - REQ: REQ-F-010
  - Archivos: `frontend/e2e/**`, `frontend/playwright.config.ts`, `frontend/package.json`, `frontend/package-lock.json`
  - Hecho cuando: `make e2e` verde contra docker compose; `make verify` verde.
