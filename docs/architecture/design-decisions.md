# Decisiones de Arquitectura

## 1. EventBridge como bus de eventos (no Kinesis, no SQS)

### Decisión
Usar Amazon EventBridge como punto de entrada para todos los eventos.

### Contexto
Necesitamos rutear eventos por tipo (page_view, cart, purchase) a distintos targets.
EventBridge permite content-based routing nativo con reglas declarativas.

### Alternativas consideradas
- **Amazon Kinesis Data Streams**: Mejor para alto throughput con ordering estricto.
  Pero requiere gestionar shards y no tiene routing nativo por contenido.
- **Amazon SQS**: Simple y confiable, pero point-to-point. No soporta fan-out
  a múltiples consumers sin SNS adicional.
- **Kafka (Confluent Cloud)**: Máximo control, replay ilimitado, ordering por partición.
  Pero mayor complejidad operativa y costo base más alto.

### Tradeoff
EventBridge sacrifica ordering estricto y replay a cambio de routing declarativo,
integración nativa con 20+ servicios AWS, y cero gestión de infraestructura.
Para un e-commerce donde el insight importa más que el orden exacto de page views, es suficiente.

---

## 2. Lambda para procesamiento (no Flink, no Step Functions)

### Decisión
Usar Lambda como capa de procesamiento event-driven.

### Contexto
Cada evento necesita: validación, enriquecimiento, escritura a DynamoDB,
envío a Firehose, y emisión de métricas a CloudWatch.

### Alternativas consideradas
- **Amazon Managed Flink**: Ideal para ventanas de tiempo y agregaciones complejas.
  Overhead alto para transformaciones simples.
- **Step Functions**: Bueno para orquestación multi-paso. Overkill para
  procesamiento stateless de un solo evento.
- **Kafka Streams**: Procesamiento en el mismo cluster Kafka. Requiere Kafka.

### Tradeoff
Lambda tiene cold starts (~100-200ms) y un límite de 15 min.
Para transformaciones sub-segundo por evento, es ideal.
Si necesitáramos agregaciones con ventanas de tiempo, Flink sería mejor opción.

---

## 3. DynamoDB + S3 (dual write pattern)

### Decisión
Escribir cada evento a DynamoDB (acceso real-time) y a S3 vía Firehose (analytics).

### Contexto
El negocio necesita dos patrones de acceso:
- Real-time: "¿cuál fue el último evento de este usuario?" → DynamoDB
- Analytics: "¿cuánto revenue por hora en los últimos 30 días?" → S3 + Athena

### Alternativas consideradas
- **Solo DynamoDB**: Posible con GSIs, pero scans costosos para analytics.
- **Solo S3**: Latencia alta para acceso real-time.
- **Redshift / Snowflake**: Potente para analytics, pero costo fijo alto.
  S3 + Athena es pay-per-query.

### Tradeoff
Dual write agrega complejidad (consistencia eventual entre stores).
TTL en DynamoDB (24h) mantiene costos controlados.
S3 con particionamiento por fecha permite queries eficientes en Athena.

---

## 4. CloudWatch como observabilidad (no Grafana, no Datadog)

### Decisión
Usar CloudWatch Dashboards y métricas custom para observabilidad.

### Contexto
Necesitamos visualizar: eventos/segundo por tipo, revenue acumulado,
latencia de procesamiento, errores.

### Alternativas consideradas
- **Grafana (self-hosted o Cloud)**: Dashboards más flexibles, mejor UX.
  Requiere infra adicional o suscripción.
- **Datadog**: Excelente para observabilidad full-stack.
  Costo por host/métrica puede escalar rápido.

### Tradeoff
CloudWatch es "good enough" y ya está integrado. Cero setup adicional.
Para un equipo que ya vive en AWS, reduce context switching.
Para equipos multi-cloud o con necesidades avanzadas de alerting, Grafana o Datadog son mejores.

---

## 5. Terraform como IaC

### Decisión
Toda la infraestructura se define en Terraform.

### Contexto
Necesitamos reproducibilidad, versionamiento, y la capacidad de destruir
y recrear el entorno completo para la demo.

### Alternativas consideradas
- **AWS CDK**: Más expresivo (TypeScript/Python), pero agrega una capa de abstracción.
- **CloudFormation**: Nativo AWS, pero verbose y sin state management propio.
- **Pulumi**: Similar a CDK, menor adopción.

### Tradeoff
Terraform es el estándar de facto para IaC multi-cloud.
El equipo ya lo usa (terraform-user). Consistencia > novedad.
