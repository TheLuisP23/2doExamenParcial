# 001 · Servicio A — tareas (modo vía rápida)

> Formato y reglas: ver [000-sistema/tasks.md](../000-sistema/tasks.md).
> **2026-11-17 — vía rápida** (plazo: despliegue antes de medianoche): las 12 tareas originales se
> consolidan en una por componente. Dentro de la tarea se mantiene TDD (pruebas primero) y trazabilidad;
> el desglose original queda en el historial git (commit `24a9bdf`).

- [ ] **TASK-A-01** — Servicio A completo: tooling, pruebas e implementación (api/dominio/repositorio), Dockerfile
  - Tipo: impl
  - Depende de: —
  - REQ: REQ-A-001, REQ-A-002, REQ-A-003, REQ-A-004, REQ-A-005, REQ-A-006, REQ-A-007, REQ-A-008, REQ-A-009, REQ-A-010, REQ-A-011, REQ-A-012, REQ-SYS-004, REQ-SYS-005, REQ-SYS-006
  - Archivos: `services/service-a/**`
  - Hecho cuando: ruff, mypy, pruebas unitarias e integración (Testcontainers) en verde con cobertura ≥ 80 %; imagen no-root construye; `make verify` verde.
