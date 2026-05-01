# Del Click al Insight: Arquitecturas Event-Driven en Tiempo Real para E-commerce

[![AWS](https://img.shields.io/badge/AWS-Event--Driven-FF9900?style=flat&logo=amazonaws)](https://aws.amazon.com/)
[![Kafka](https://img.shields.io/badge/Apache-Kafka-231F20?style=flat&logo=apachekafka)](https://kafka.apache.org/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?style=flat&logo=terraform)](https://www.terraform.io/)
[![ACM](https://img.shields.io/badge/ACM%20Week%202026-Bogotá-blue)](https://www.acm.org/)

En e-commerce, reaccionar tarde puede significar perder una oportunidad. Esta plataforma event-driven
demuestra cómo transformar un simple clic en un insight accionable dentro de una plataforma de datos,
respondiendo al comportamiento del usuario en tiempo real.

Proyecto y demo para la charla en **ACM Week 2026 — Bogotá**.

---

## Problema

Un e-commerce genera miles de eventos por segundo: page views, interacciones con el carrito y compras.
El negocio necesita **insights en tiempo real** para tomar decisiones: ¿qué producto está trending?,
¿hay un drop en el checkout?, ¿cuánto revenue llevamos en la última hora?

El desafío técnico: procesar estos eventos con baja latencia, de forma escalable,
desacoplada y resiliente — sin que los productores se rompan cuando el backend evoluciona.

---

## Las tres piezas clave

### 1. Ingesta y enrutamiento de eventos
Capturar cada interacción del usuario y dirigirla al destino correcto con baja latencia,
usando Apache Kafka como backbone de mensajería y AWS Route 53 para resolución de tráfico.

### 2. Procesamiento asíncrono
Transformar, validar y enriquecer eventos de forma desacoplada mediante AWS Lambda,
permitiendo que los productores evolucionen independientemente del backend.

### 3. Observabilidad de punta a punta
Monitorear la salud del sistema en tiempo real con Grafana, detectando anomalías
y midiendo métricas de negocio desde el primer evento hasta el insight final.

---

## Arquitectura

```
                                                          ┌──────────────┐
                                                     ┌───▶│  Amazon      │
                                                     │    │  DynamoDB    │
                                                     │    │  (Real-time) │
                                                     │    └──────────────┘
                                                     │          ▲
                                                     │    ┌─────┴────────┐
┌─────────────┐     ┌──────────────┐     ┌───────────┴─┐  │   Circuit    │
│  Event      │────▶│  Apache      │────▶│  AWS Lambda  │──┤   Breaker    │
│  Producers  │     │  Kafka       │     │  (Transform  │  │  (Degrade    │
│  (Python)   │     │              │     │   + Enrich)  │  │   Gracefully)│
└─────────────┘     └──────┬───────┘     └──┬───────┬──┘  └──────────────┘
       ▲                   │                │       │
       │                   │                │       ▼
  Route 53                 │                │ ┌─────────────────┐  ┌──────────────┐
  (DNS routing)            │                │ │  Amazon Kinesis  │─▶│  S3 + Athena │
                           │                │ │  Data Firehose   │  │  (Analytics) │
                           │                │ └─────────────────┘  └──────────────┘
                           │                │
                           ▼                ▼
                    ┌─────────────────┐  ┌─────────────┐
                    │  Grafana        │  │  Amazon SQS  │
                    │  (Metrics +     │  │  (DLQ)       │
                    │   Dashboards +  │  │  ⚠ Alarma    │
                    │   Alerts)       │  └──────┬──────┘
                    └─────────────────┘◀────────┘
```

### Flujo del evento

1. **Click** — El producer (Python) genera eventos de e-commerce (page view, cart, purchase)
2. **Route** — AWS Route 53 resuelve el tráfico hacia el endpoint de ingesta
3. **Ingest** — Apache Kafka recibe y rutea eventos por tipo usando topics
4. **Process** — Lambda transforma, valida y enriquece cada evento de forma asíncrona
5. **Store** — DynamoDB para acceso real-time, S3 vía Firehose para analytics
6. **Insight** — Grafana dashboards muestran métricas de negocio en vivo

### Resiliencia

- **Circuit Breaker** — Si DynamoDB falla, Lambda deja de escribir ahí (circuito abierto) pero sigue enviando a Firehose y emitiendo métricas. Cuando DynamoDB se recupera, el circuito se cierra automáticamente.
- **Dead Letter Queue** — Eventos que Lambda no puede procesar van a SQS (14 días de retención) para investigación y reprocesamiento.
- **Alarmas** — Grafana alerta cuando hay errores de Lambda, throttling, o mensajes en la DLQ.

---

## Stack tecnológico

| Capa | Tecnología | Alternativa AWS nativa | Tradeoff clave |
|------|------------|------------------------|----------------|
| DNS / Routing | AWS Route 53 | ALB / API Gateway | Control de tráfico global vs simplicidad |
| Ingestion | Apache Kafka | Amazon EventBridge | Control de ordering y replay vs costo operativo |
| Processing | AWS Lambda (Python) | Kafka Streams / Flink | Latencia vs complejidad operativa |
| Storage RT | Amazon DynamoDB | Redis / ElastiCache | Costo vs flexibilidad de queries |
| Storage Analytics | S3 + Athena | Redshift / Snowflake | Costo vs performance en queries complejas |
| Observability | Grafana | Amazon CloudWatch | Ecosistema unificado vs vendor lock-in |

---

## Estructura del repo

```
click-to-insight-ecommerce/
├── infrastructure/          # Terraform — toda la infra
├── src/
│   ├── producers/           # Generadores de eventos (Python)
│   └── lambdas/             # Funciones de procesamiento
├── schemas/                 # Contratos de eventos (JSON Schema)
├── docs/
│   ├── architecture/        # Diagramas y decisiones de diseño
│   ├── well-architected/    # Mapeo al AWS Well-Architected Framework
│   ├── tradeoffs/           # Análisis de alternativas por capa
│   ├── lessons-learned/     # Lecciones aprendidas
│   └── demo/                # Runbook y guía de la demo en vivo
├── dashboards/              # Definiciones de dashboards Grafana
└── tests/                   # Tests de integración
```

---

## Quick Start

### Pre-requisitos

- AWS CLI configurado (región: us-east-2)
- Terraform >= 1.5
- Python >= 3.12
- Apache Kafka (local o Confluent Cloud)

### Deploy

```bash
cd infrastructure
terraform init
terraform apply

# Ejecutar el producer
cd ../src/producers
python event_producer.py
```

### Demo en vivo

Ver [docs/demo/runbook.md](docs/demo/runbook.md) para el paso a paso completo.

---

## Well-Architected Framework

Este proyecto está mapeado a los 6 pilares del AWS Well-Architected Framework.
Ver [docs/well-architected/](docs/well-architected/) para el análisis completo.

---

## Contexto

Charla presentada en ACM Week 2026, Bogotá, Colombia.
Organizada por la Association for Computing Machinery.

**Speaker:** Rocío Baigorria — Data Engineer especializada en arquitecturas event-driven y AWS.

---

*Del click al insight. Build on, always.*
