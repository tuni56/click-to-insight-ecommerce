# AWS-Native vs Multi-Cloud: La Realidad de Producción

## Por qué esta demo es AWS-native

Esta arquitectura usa servicios 100% AWS porque es una demo para una charla:
se levanta en 3 minutos con `terraform apply`, se destruye limpia, y permite
enfocarse en los **patrones** sin distraerse configurando infraestructura.

Pero la realidad de la industria es otra.

---

## La realidad: multi-cloud y Kafka

El ~90% de las empresas opera en entornos multi-cloud (AWS + GCP, AWS + Azure, hybrid con on-prem).
En ese contexto, atarte a EventBridge significa atarte a un solo cloud para tu capa de mensajería.

**Apache Kafka es el estándar de facto** para arquitecturas event-driven en producción:

- Protocolo abierto — sin vendor lock-in
- Ordering estricto por partición
- Replay configurable (días, semanas, indefinido)
- Ecosistema maduro: Connect, Streams, Schema Registry, ksqlDB
- Funciona en cualquier cloud o on-prem
- Confluent Cloud, Amazon MSK, Aiven, Redpanda como opciones managed

---

## Mapeo: Demo vs Producción Multi-Cloud

| Capa | Demo (AWS-native) | Producción multi-cloud |
|------|-------------------|----------------------|
| Event Bus | EventBridge | **Apache Kafka** (Confluent / MSK / Redpanda) |
| Processing | Lambda | **Kafka Streams / Apache Flink** |
| Schema Registry | JSON Schemas en repo | **Confluent Schema Registry** (Avro/Protobuf) |
| Storage RT | DynamoDB | PostgreSQL / Redis / el DB del cloud donde estés |
| Storage Analytics | S3 + Athena | Data lake (S3/GCS/ADLS) + Spark / Trino |
| Observability | CloudWatch | **Grafana + Prometheus** |
| IaC | Terraform | Terraform (funciona en todos los clouds) |

---

## Lo que NO cambia

Los patrones de arquitectura event-driven son independientes del proveedor:

- **Pub/Sub y desacoplamiento** — Producers no conocen a los consumers. Funciona igual con EventBridge, Kafka, o Google Pub/Sub.
- **Schema contracts** — El contrato del evento es el mismo sea JSON Schema, Avro, o Protobuf.
- **Circuit Breaker** — Protege escrituras a downstream sin importar si es DynamoDB, PostgreSQL, o Redis.
- **Dead Letter Queue** — Captura eventos fallidos. En Kafka se implementa con un topic dedicado (`.dlq`).
- **Dual write (real-time + analytics)** — El patrón CQRS aplica en cualquier stack.
- **Observabilidad con métricas custom** — `DynamoCircuitOpen` en CloudWatch es lo mismo que un gauge en Prometheus.

**Los servicios son reemplazables. Los patrones no.**

---

## Cuándo elegir cada approach

### AWS-native (EventBridge + Lambda)
- Equipo 100% en AWS sin planes de migrar
- Volumen < 100K eventos/segundo
- Prioridad: time-to-market y zero-ops
- Equipo pequeño sin expertise en Kafka

### Multi-cloud (Kafka + Flink/Streams)
- Operación en múltiples clouds o hybrid
- Necesidad de ordering estricto y replay
- Volumen alto (millones de eventos/segundo)
- Equipo con expertise en streaming
- Estrategia de evitar vendor lock-in

---

## El mensaje para la audiencia

> "Lo que ven hoy es una implementación en AWS porque me permite mostrarles
> los conceptos en vivo sin gastar 20 minutos configurando un cluster Kafka.
> Pero si mañana mueven esto a Kafka + Flink + Grafana, los patrones que
> vieron — el desacoplamiento, el circuit breaker, la DLQ, el dual write —
> son exactamente los mismos. Eso es lo que se llevan hoy."
