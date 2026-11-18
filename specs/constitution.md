# Constitución del proyecto

> Principios **no negociables**. Una spec, plan, tarea o PR que contradiga un principio se
> rechaza o se cambia primero la constitución mediante un ADR aprobado por un humano.
> Versión: 1.0.0 · Ratificada: 2026-11-17

## I. Independencia de servicios
1. Servicio A y servicio B **no comparten** base de datos, código, librerías internas,
   imágenes ni esquemas.
2. **No se llaman entre sí** (ni HTTP, ni colas, ni BD). Cualquier composición de datos
   (p. ej. socio + libro en un préstamo) la hace el **frontend**.
3. Las referencias entre dominios son **identificadores opacos** (B guarda `book_id` sin
   validarlo contra A).
4. Cada servicio se construye, prueba, versiona y despliega por separado.

## II. Base de datos por servicio
1. A → PostgreSQL 16; B → MongoDB 7. Cada BD solo es accesible por su servicio.
2. Credenciales distintas por servicio. Esquema versionado (migraciones/índices en código).

## III. Contrato primero
1. Todo endpoint existe primero en `specs/NNN-*/contracts/openapi.yaml` (OpenAPI 3.1).
2. El código se ajusta al contrato, no al revés; cambiar el contrato requiere actualizar
   spec y tests de contrato en el mismo cambio.
3. Errores en `application/problem+json` (RFC 9457).

## IV. TDD y trazabilidad
1. Las pruebas se escriben **antes** que la implementación (tareas de test preceden a las de código).
2. Todo requisito `REQ-*` en alcance tiene al menos una prueba que lo referencia; toda prueba
   referencia al menos un `REQ-*` existente.
3. Cobertura de líneas **≥ 80 %** por servicio y frontend (unitarias + integración).
4. "Hecho" significa `make verify` en verde. La afirmación de un agente no es evidencia.

## V. Twelve-Factor
1. Configuración **solo** por variables de entorno; el proceso falla al arrancar si falta una obligatoria.
2. Procesos sin estado; el estado vive en la BD del servicio.
3. Logs a stdout en **JSON** (una línea por evento, con `timestamp`, `level`, `message`,
   `service`, `request_id`).
4. Paridad dev/prod: misma imagen en docker-compose y EKS; solo cambian variables.

## VI. Seguridad
1. **Sin secretos en el repositorio** (gitleaks en pre-commit y CI). Solo `.env.example` con valores ficticios.
2. Imágenes **no-root**, base con versión fijada, multi-stage, sin herramientas de build en runtime.
3. GitHub Actions se autentica en AWS con **OIDC**; prohibidas las access keys estáticas.
4. Mínimo privilegio en IAM y en Kubernetes.

## VII. Operabilidad
1. Cada servicio expone `GET /health/live` (proceso vivo, sin dependencias) y
   `GET /health/ready` (dependencias listas, p. ej. BD) → `200` o `503`.
2. **Todo** contenedor en Kubernetes declara `resources.requests` y `resources.limits`
   (CPU y memoria) y probes de liveness/readiness.
3. Manifiestos YAML planos (sin Helm ni Kustomize) validados con kubeconform.

## VIII. Alcance y proceso
1. Una tarea a la vez (WIP = 1); una tarea solo toca los archivos que declara.
2. Cada spec declara "Fuera de alcance". Lo ambiguo se marca `[NEEDS CLARIFICATION]` y se pregunta.
3. Commits pequeños con Conventional Commits; git es el historial.
4. `feature_list.json` es append-only: solo `passes`/evidencia cambian, y solo tras verificar.

## Gobierno
- Enmiendas: ADR en `docs/adr/` + incremento de versión semántica de este documento.
- El subagente `spec-reviewer` verifica cumplimiento de la constitución en cada spec/plan.
