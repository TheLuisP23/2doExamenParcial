# 0003 — Bases de datos dentro del clúster (StatefulSet + EBS gp3)

- **Estado**: Propuesto · **Fecha**: 2026-11-17 · **Relacionado**: REQ-P-007, REQ-P-008, REQ-P-009

## Contexto
El enunciado exige las BD dentro del clúster. Las alternativas gestionadas (RDS, DocumentDB) añadirían
coste y recursos fuera del clúster.

## Decisión
PostgreSQL y MongoDB corren como StatefulSets de 1 réplica con `volumeClaimTemplates` sobre una
StorageClass `gp3` (driver `aws-ebs-csi-driver`, addon gestionado por eksctl con IRSA),
`WaitForFirstConsumer` y cifrado.

## Alternativas consideradas
- **RDS / DocumentDB**: HA y backups gestionados, pero fuera de alcance y más caros.
- **emptyDir / hostPath**: sin persistencia real si el pod se reprograma.

## Consecuencias
- (+) Todo el sistema se crea y se destruye con el clúster; coste bajo.
- (−) Sin HA ni backups: perder el volumen EBS es perder los datos (aceptable en entorno académico).
- (−) Un volumen EBS está atado a una AZ: el pod de BD solo puede reprogramarse en nodos de esa AZ.
- (−) `reclaimPolicy: Delete` → `make infra-down` borra los datos (intencional).
