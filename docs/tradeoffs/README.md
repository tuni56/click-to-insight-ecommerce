# Tradeoffs: AWS Managed vs Alternativas

## Ingestion: EventBridge vs Kafka (Confluent Cloud)

| Criterio | EventBridge | Kafka (Confluent Cloud) |
|----------|-------------|------------------------|
| Setup | 0 — un API call | Cluster provisioning, topics, ACLs |
| Ordering | No garantizado | Por partición |
| Replay | 24h archive | Retención configurable (∞) |
| Routing | Content-based rules nativo | Consumer-side filtering |
| Throughput | Soft limit ~10K/s (ampliable) | Millones/s |
| Costo base | $0 (pay per event) | ~$200/mes mínimo |
| Lock-in | Alto (API propietaria) | Bajo (protocolo abierto) |

**Cuándo elegir Kafka**: Necesitas ordering estricto, replay de días/semanas,
o ya tienes un equipo con expertise en Kafka.

**Cuándo elegir EventBridge**: Quieres empezar rápido, tu volumen es < 100K eventos/s,
y valoras la integración nativa con AWS.

---

## Processing: Lambda vs Kafka Streams vs Flink

| Criterio | Lambda | Kafka Streams | Managed Flink |
|----------|--------|---------------|---------------|
| Modelo | Event-driven, stateless | Stream processing, stateful | Stream processing, stateful |
| Latencia | 100-200ms (cold start) | Sub-ms (hot) | Sub-segundo |
| Ventanas de tiempo | Manual (con DynamoDB) | Nativo | Nativo |
| Scaling | Automático | Manual (instances) | Automático |
| Costo | Per-invocation | Per-instance | Per-KPU |
| Complejidad | Baja | Media | Alta |

**Cuándo elegir Flink**: Agregaciones con ventanas, joins entre streams, CEP.

**Cuándo elegir Lambda**: Transformaciones simples, enriquecimiento, fan-out.

---

## Observability: CloudWatch vs Grafana vs Datadog

| Criterio | CloudWatch | Grafana Cloud | Datadog |
|----------|------------|---------------|---------|
| Setup en AWS | 0 | Datasource config | Agent install |
| Dashboards | Funcionales | Excelentes | Excelentes |
| Alerting | Básico | Avanzado | Avanzado |
| Multi-cloud | No | Sí | Sí |
| Costo | Incluido (métricas custom extra) | Free tier + paid | Per-host pricing |
| Correlación logs-metrics-traces | Limitada | Buena (con Loki+Tempo) | Excelente |

**Cuándo elegir Grafana/Datadog**: Equipo multi-cloud, necesitas correlación
avanzada, o el equipo ya los usa.

**Cuándo elegir CloudWatch**: 100% AWS, equipo pequeño, quieres simplicidad.

---

## Storage: DynamoDB vs Redis | S3+Athena vs Redshift

### Real-time store

| Criterio | DynamoDB | ElastiCache (Redis) |
|----------|----------|---------------------|
| Latencia | Single-digit ms | Sub-ms |
| Persistencia | Sí | Opcional |
| Costo | Per-request | Per-node (siempre encendido) |
| TTL nativo | Sí | Sí |
| Queries | Key-value + GSI | Key-value + data structures |

### Analytics store

| Criterio | S3 + Athena | Redshift Serverless |
|----------|-------------|---------------------|
| Costo | $5/TB scanned | $0.375/RPU-hour |
| Performance | Segundos | Sub-segundo |
| Concurrencia | Alta | Media |
| Setup | Bajo | Medio |
