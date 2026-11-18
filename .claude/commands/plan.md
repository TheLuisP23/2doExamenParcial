---
description: Escribir el plan técnico (cómo) de una spec ya revisada
argument-hint: <carpeta de spec, p. ej. 001-servicio-a>
---

Fase SDD 2/6 para `specs/$ARGUMENTS`. No escribas código.

1. Verifica que `spec.md` no tenga `[NEEDS CLARIFICATION]` que afecten al diseño. Si los hay,
   pregunta al usuario y detente (o documenta la suposición explícita en el plan y en PROGRESS.md › Decisiones).
2. Escribe/actualiza `plan.md` con:
   - Stack con versión y motivo; estructura de carpetas; **capas api / dominio / repositorio** y reglas de dependencia.
   - Configuración (tabla de variables de entorno, obligatorias y por defecto).
   - **Estrategia de pruebas**: unitarias, integración (Testcontainers), contrato (schemathesis o equivalente),
     e2e (Playwright) y smoke; comando exacto que ejecutará `make verify` para cada nivel.
   - Convención de trazabilidad (`@pytest.mark.req("REQ-…")` / `[REQ-…]` en títulos).
   - Riesgos y decisiones; si una decisión es arquitectónica, crea un ADR en `docs/adr/` desde la plantilla.
3. Comprueba que el plan respeta `specs/constitution.md` (independencia, BD por servicio, 12-factor, no-root, probes, requests/limits).
4. Lanza **spec-reviewer** (modo plan) y aplica lo bloqueante. Resume y detente.
