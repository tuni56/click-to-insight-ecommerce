# Demo Runbook — Del Click al Insight

## Pre-requisitos

- AWS CLI configurado con perfil que tenga acceso a us-east-2
- Terraform >= 1.5
- Python >= 3.12 con boto3

---

## 1. Deploy de la infraestructura

```bash
cd infrastructure
terraform init
terraform apply -auto-approve
```

Tiempo estimado: ~2-3 minutos.

Outputs esperados:
- event_bus_name = "click-to-insight-events"
- lambda_function = "click-to-insight-process-event"
- dynamodb_table = "click-to-insight-events"
- s3_bucket = "click-to-insight-events-lake-<ACCOUNT_ID>"
- firehose_stream = "click-to-insight-events-to-s3"

---

## 2. Abrir el CloudWatch Dashboard

1. Ir a CloudWatch → Dashboards (us-east-2)
2. Abrir el dashboard "ecommerce-realtime" (creado por Terraform)
3. Configurar auto-refresh cada 10 segundos

---

## 3. Ejecutar el producer

```bash
cd src/producers
python event_producer.py
```

Deberías ver:
```
🚀 Producing events to EventBridge bus 'click-to-insight-events' in us-east-2
   Ctrl+C to stop

  [page_view   ] user=user_3  id=a1b2c3d4
  [cart_event   ] user=user_7  id=e5f6g7h8
  [purchase     ] user=user_1  id=i9j0k1l2
  --- batch sent (9 total) ---
```

---

## 4. Verificar el flujo completo

### EventBridge
```bash
aws events describe-event-bus --name click-to-insight-events --region us-east-2
```

### Lambda (logs)
```bash
aws logs tail /aws/lambda/click-to-insight-process-event --region us-east-2 --follow
```

### DynamoDB (últimos eventos)
```bash
aws dynamodb scan --table-name click-to-insight-events --region us-east-2 --limit 5
```

### S3 (datos para analytics)
```bash
aws s3 ls s3://click-to-insight-events-lake-<ACCOUNT_ID>/events/ --recursive --region us-east-2
```

---

## 5. Narrativa de la demo

| Paso | Qué mostrar | Qué decir |
|------|-------------|-----------|
| 1 | Terminal con producer | "Estos son los clicks — cada segundo, el e-commerce genera page views, cart events y purchases" |
| 2 | CloudWatch Dashboard | "Y acá está el insight — en tiempo real vemos revenue acumulado, eventos por tipo, y podemos detectar anomalías" |
| 3 | Diagrama de arquitectura | "Entre el click y el insight hay 5 servicios AWS, todos serverless, todos desacoplados" |
| 4 | Código del producer | "El producer no sabe nada del backend. Solo manda eventos a EventBridge. Si mañana cambio Lambda por Flink, el producer no se entera" |
| 5 | Terraform | "Y toda esta infra se crea y destruye en 3 minutos con Terraform" |

---

## 6. Teardown

```bash
cd infrastructure
terraform destroy -auto-approve
```

⚠️ Esto elimina TODOS los recursos. Los datos en DynamoDB y S3 se pierden.

---

## 7. Troubleshooting

**Producer falla con AccessDenied**
```bash
aws sts get-caller-identity  # verificar identidad
aws events describe-event-bus --name click-to-insight-events --region us-east-2  # verificar bus existe
```

**Lambda no se invoca**
- Verificar la regla de EventBridge en la consola
- Revisar CloudWatch Logs del Lambda

**No hay datos en S3**
- Firehose bufferea por 60 segundos. Esperar al menos 1 minuto.
- Verificar el delivery stream en la consola de Kinesis Firehose.

**Dashboard vacío**
- Las métricas custom tardan ~1-2 minutos en aparecer.
- Verificar namespace "Ecommerce/Events" en CloudWatch Metrics.
