# Lecciones Aprendidas

## 1. Empezar serverless, migrar si duele

Empezamos con EventBridge + Lambda porque el time-to-market era prioridad.
Si el volumen crece a >100K eventos/s o necesitamos ordering estricto,
la migración a Kinesis o Kafka es un cambio de ingestion layer, no de toda la plataforma.

**Lección**: El desacoplamiento por capas hace que las migraciones sean locales, no globales.

---

## 2. El schema es el contrato

Definir JSON Schemas desde el día 1 evitó problemas de compatibilidad
entre el producer y los consumers. Cuando agregamos `product_name` al cart event,
el schema nos obligó a hacerlo backward-compatible.

**Lección**: Sin schema explícito, los eventos se convierten en "lo que sea que mande el frontend".

---

## 3. Dual write tiene un costo

Escribir a DynamoDB Y a Firehose desde la misma Lambda simplifica el código
pero introduce consistencia eventual. Si Firehose falla, DynamoDB tiene el dato pero S3 no.

**Lección**: Para este caso (analytics no es mission-critical) es aceptable.
Para financial data, considerar transactional outbox pattern.

---

## 4. CloudWatch es suficiente hasta que no lo es

Para la demo y un equipo pequeño, CloudWatch cumple. Pero la falta de
correlación logs-metrics-traces se siente rápido en producción.

**Lección**: Empezar con CloudWatch, tener el plan de migración a Grafana/Datadog documentado.

---

## 5. Terraform destroy es tu mejor amigo en demos

Poder destruir y recrear toda la infra en 3 minutos da confianza para experimentar.
También garantiza que la demo siempre parte de un estado limpio.

**Lección**: Si no puedes hacer `terraform destroy && terraform apply` y que todo funcione,
tu IaC está incompleta.

---

## 6. El "insight" es lo que vende la arquitectura

La audiencia no se emociona con "eventos llegando a un bus".
Se emociona cuando ve un dashboard moverse en tiempo real mostrando revenue.
El insight es el producto; la arquitectura es el medio.

**Lección**: Diseñar la demo de atrás para adelante — empezar por el insight que quieres mostrar.
