# 0002 — Base de datos por servicio

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: constitución II, REQ-SYS-002, REQ-P-018

## Contexto
Los servicios deben poder evolucionar y desplegarse de forma independiente. Compartir BD crea
acoplamiento de esquema y de disponibilidad.

## Decisión
A usa PostgreSQL 16 y B usa MongoDB 7, cada uno con su StatefulSet, Secret, credenciales y Service.
Ningún servicio conoce la cadena de conexión del otro. Las NetworkPolicies impiden el acceso cruzado.
Las referencias entre dominios (`book_id` en préstamos) son identificadores opacos sin integridad referencial.

## Alternativas consideradas
- **Una BD compartida con esquemas separados**: más barato, pero acopla y viola la constitución.
- **Llamada síncrona B → A para validar `book_id`**: prohibida por el enunciado (no se llaman entre sí).

## Consecuencias
- (+) Autonomía total; tecnología adecuada a cada modelo (relacional vs documental).
- (−) Sin consistencia entre A y B: un préstamo puede apuntar a un libro borrado
  (el front muestra "Libro no disponible", REQ-F-006). Ver Q-A-4.
- (−) Dos motores que operar.
