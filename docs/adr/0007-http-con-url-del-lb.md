# 0007 — Solo HTTP con la URL del LoadBalancer (sin TLS)

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: REQ-P-011, spec 000 "Fuera de alcance"

## Contexto
No hay dominio propio. Un certificado ACM requiere un dominio validado, e Ingress está excluido.

## Decisión
El front se expone con un Service `type: LoadBalancer` en el puerto 80; la URL pública es el DNS
generado por AWS (`*.elb.amazonaws.com`). Sin TLS, sin dominio, sin Ingress.

## Justificación
Alcance académico, entorno efímero (se destruye tras las pruebas), sin datos personales reales ni
autenticación. El coste y la complejidad de dominio + ACM + controlador no aportan a los objetivos de aprendizaje.

## Consecuencias
- (−) Tráfico en claro: **no** usar datos reales (documentado en el README).
- (−) La URL cambia en cada `infra-up` → los smoke tests la obtienen con `kubectl get svc`.
- Camino de evolución: Route 53 + ACM + anotaciones de LB o AWS Load Balancer Controller (nuevo ADR).
