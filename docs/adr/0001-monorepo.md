# 0001 — Monorepo

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: constitución I, VIII

## Contexto
Dos servicios, un frontend e infraestructura los mantiene un equipo pequeño (y agentes de IA) en un
proyecto académico. El harness (specs, trazabilidad, `make verify`) necesita ver todo el sistema a la vez.

## Decisión
Un único repositorio con `services/service-a`, `services/service-b`, `frontend`, `deploy`, `specs`, `docs`.
La independencia se garantiza con reglas, no con repos separados: sin código compartido entre carpetas
de servicios, manifiestos y pipelines separables por componente, pruebas de arquitectura (REQ-SYS-002).

## Alternativas consideradas
- **Polyrepo** (un repo por componente): independencia física, pero triplica CI, dificulta la
  trazabilidad cruzada y reduce el contexto disponible para los agentes.

## Consecuencias
- (+) Un solo `make verify`, una sola fuente de specs, cambios atómicos contrato + código + test.
- (−) Riesgo de acoplamiento accidental (imports cruzados) → mitigado por `tests/system/test_independence.py`.
- (−) CI construye más de lo necesario → mitigable con filtros por ruta (Q-P-6).
