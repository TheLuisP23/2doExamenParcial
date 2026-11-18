# 0004 — Frontend con proxy reverso Nginx (sin CORS)

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: REQ-SYS-001, REQ-F-008, REQ-F-009

## Contexto
El navegador necesita hablar con dos APIs. Exponerlas en orígenes distintos obliga a configurar CORS
y a publicar más de un LoadBalancer.

## Decisión
Nginx sirve la SPA y hace de proxy: `/api/a/*` → servicio A y `/api/b/*` → servicio B, quitando el
prefijo. Hay un único Service `LoadBalancer` (el del front). Los upstreams se configuran por variables
de entorno mediante las plantillas `envsubst` de la imagen oficial `nginx-unprivileged`.

## Alternativas consideradas
- **CORS + un LB por servicio**: más superficie pública, más coste, configuración CORS frágil.
- **Ingress + AWS Load Balancer Controller**: excluido por el enunciado.
- **BFF propio**: añadiría un tercer servicio con lógica.

## Consecuencias
- (+) Origen único, sin CORS; A y B solo son accesibles dentro del clúster.
- (+) Los servicios no conocen el prefijo (el contrato se escribe en `/books`, `/members`).
- (−) Nginx es el punto único de entrada → 2 réplicas y probes.
