# Del Click al Insight: Arquitecturas Event-Driven en Tiempo Real para E-commerce

[![AWS](https://img.shields.io/badge/AWS-Event--Driven-FF9900?style=flat&logo=amazonaws)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?style=flat&logo=terraform)](https://www.terraform.io/)
[![ACM](https://img.shields.io/badge/ACM%20Week%202026-Bogotá-blue)](https://www.acm.org/)

Plataforma event-driven en tiempo real para e-commerce, construida 100% con servicios AWS.
Proyecto y demo para la charla en **ACM Week 2026 — Bogotá**.

---

## Problema

Un e-commerce genera miles de eventos por segundo: page views, interacciones con el carrito y compras.
El negocio necesita **insights en tiempo real** para tomar decisiones: ¿qué producto está trending?,
¿hay un drop en el checkout?, ¿cuánto revenue llevamos en la última hora?

El desafío técnico: procesar estos eventos con baja latencia, de forma escalable,
desacoplada y resiliente — sin que los productores se rompan cuando el backend evoluciona.

---

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Event      │────▶│  Amazon      │────▶│  AWS Lambda      │────▶│  Amazon      │
│  Producers  │     │  EventBridge │     │  (Transform +    │     │  DynamoDB    │
│  (Python)   │     │              │     │   Enrich)        │     │  (Real-time) │
└─────────────┘     └──────┬───────┘     └────────┬────────┘     └──────────────┘
                           │                      │
                           │                      ▼
                           │              ┌─────────────────┐     ┌──────────────┐
                           │              │  Amazon Kinesis  │────▶│  S3 + Athena │
                           │              │  Data Firehose   │     │  (Analytics) │
                           │              └─────────────────┘     └──────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │  Amazon         │
                    │  CloudWatch     │
                    │  (Dashboards)   │
                    └─────────────────┘
```

### Flujo del evento

1. **Click** — El producer genera eventos de e-commerce (page view, cart, purchase)
2. **Ingest** — EventBridge recibe y rutea eventos por tipo usando reglas
3. **Process** — Lambda transforma, valida y enriquece cada evento
4. **Store** — DynamoDB para acceso real-time, S3 vía Firehose para analytics
5. **Insight** — CloudWatch dashboards muestran métricas de negocio en vivo

---

## Alternativas por capa

| Capa | AWS (este repo) | Alternativa | Tradeoff clave |
|------|-----------------|-------------|----------------|
| Ingestion | EventBridge | Kafka (Confluent Cloud) | Costo vs control de ordering y replay |
| Processing | Lambda | Kafka Streams / Flink | Latencia vs complejidad operativa |
| Storage RT | DynamoDB | Redis / ElastiCache | Costo vs flexibilidad de queries |
| Storage Analytics | S3 + Athena | Redshift / Snowflake | Costo vs performance en queries complejas |
| Observability | CloudWatch | Grafana / Datadog | Vendor lock-in vs ecosistema unificado |

---

## Estructura del repo

```
click-to-insight-ecommerce/
├── infrastructure/          # Terraform — toda la infra AWS
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
├── dashboards/              # Definiciones de CloudWatch dashboards
└── tests/                   # Tests de integración
```

---

## Quick Start

### Pre-requisitos

- AWS CLI configurado (región: us-east-2)
- Terraform >= 1.5
- Python >= 3.12

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

**Speaker:** Rocío — Data Engineer especializada en arquitecturas event-driven y AWS.

---

*Del click al insight. Build on, always.*
