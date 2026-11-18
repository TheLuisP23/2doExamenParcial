# 002 · Servicio B — tareas (modo vía rápida)

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md).
> **2026-11-17 — vía rápida**: las 14 tareas originales se consolidan en una (desglose original en el commit `24a9bdf`).

- [x] **TASK-B-01** — Servicio B completo: tooling, pruebas e implementación (api/dominio/repositorio), Dockerfile
  - Tipo: impl
  - Depende de: —
  - REQ: REQ-B-001, REQ-B-002, REQ-B-003, REQ-B-004, REQ-B-005, REQ-B-006, REQ-B-007, REQ-B-008, REQ-B-009, REQ-B-010, REQ-B-011, REQ-B-012, REQ-B-013, REQ-B-014, REQ-B-015
  - Archivos: `services/service-b/**`
  - Hecho cuando: lint, typecheck, pruebas unitarias e integración en verde con cobertura ≥ 80 %; imagen no-root construye; `make verify` verde.
