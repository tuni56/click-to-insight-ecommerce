# AWS Well-Architected Framework — Mapeo del Proyecto

## 1. Excelencia Operativa

| Práctica | Implementación |
|----------|---------------|
| IaC | Terraform — infra versionada y reproducible |
| Observabilidad | CloudWatch métricas custom + dashboards |
| Runbooks | docs/demo/runbook.md con pasos de deploy y troubleshooting |
| Evolución incremental | EventBridge rules permiten agregar targets sin tocar producers |

**Alternativa**: Datadog o Grafana para dashboards más ricos y alerting avanzado.

---

## 2. Seguridad

| Práctica | Implementación |
|----------|---------------|
| Least privilege | IAM roles con permisos mínimos por servicio |
| Encryption at rest | DynamoDB y S3 encriptan por defecto |
| Encryption in transit | EventBridge, Lambda, Firehose usan TLS |
| No secrets en código | Variables de entorno en Lambda, no hardcoded |

**Mejora futura**: Validación de schemas en EventBridge (Schema Registry).

---

## 3. Confiabilidad

| Práctica | Implementación |
|----------|---------------|
| Desacoplamiento | EventBridge desacopla producers de consumers |
| Retry automático | EventBridge retry policy + Lambda DLQ |
| Multi-AZ | DynamoDB, S3, Lambda son multi-AZ por defecto |
| Idempotencia | event_id como partition key previene duplicados |

**Alternativa**: Kafka (Confluent Cloud) para replay completo de eventos.
EventBridge retiene eventos 24h; Kafka puede retener indefinidamente.

---

## 4. Eficiencia de Performance

| Práctica | Implementación |
|----------|---------------|
| Serverless | Lambda escala automáticamente con la carga |
| On-demand | DynamoDB PAY_PER_REQUEST, sin capacity planning |
| Batch writes | Firehose bufferea antes de escribir a S3 |
| Particionamiento | S3 particionado por year/month/day para Athena |

**Tradeoff**: Lambda cold starts (~100-200ms). Aceptable para este caso.
Para sub-10ms, considerar Kinesis + Flink.

---

## 5. Optimización de Costos

| Práctica | Implementación |
|----------|---------------|
| Pay-per-use | Todos los servicios son serverless/on-demand |
| TTL | DynamoDB TTL de 24h elimina datos viejos automáticamente |
| Athena | Pay-per-query en lugar de cluster siempre encendido |
| Firehose buffering | Reduce número de PUTs a S3 |

**Estimación para demo**: < $5 USD/mes con tráfico de prueba.
**Estimación producción**: Depende del volumen. EventBridge $1/M eventos,
Lambda $0.20/M invocaciones, DynamoDB ~$1.25/M writes.

---

## 6. Sostenibilidad

| Práctica | Implementación |
|----------|---------------|
| Serverless | Sin servidores idle consumiendo energía |
| Right-sizing | Lambda 256MB, ajustado al workload |
| Data lifecycle | TTL en DynamoDB, S3 lifecycle policies (futuro) |

**Mejora futura**: S3 Intelligent-Tiering para datos históricos.
