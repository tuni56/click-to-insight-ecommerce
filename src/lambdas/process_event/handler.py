import json
import os
import time
from decimal import Decimal
import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-2"))
firehose = boto3.client("firehose", region_name=os.environ.get("AWS_REGION", "us-east-2"))
cloudwatch = boto3.client("cloudwatch", region_name=os.environ.get("AWS_REGION", "us-east-2"))

TABLE_NAME = os.environ.get("TABLE_NAME", "ecommerce-events")
FIREHOSE_STREAM = os.environ.get("FIREHOSE_STREAM", "ecommerce-events-to-s3")

table = dynamodb.Table(TABLE_NAME)


# ---------------------------------------------------------------------------
# Circuit Breaker — protects DynamoDB writes
#
# States:
#   CLOSED   → normal operation, writes go to DynamoDB
#   OPEN     → DynamoDB is failing, skip writes (degrade gracefully)
#   HALF_OPEN → try one write to see if DynamoDB recovered
#
# Lives in module-level globals so state persists across warm Lambda
# invocations (same execution environment).  A cold start resets to CLOSED,
# which is the safe default — if DynamoDB is still down the breaker will
# re-open after FAILURE_THRESHOLD failures.
# ---------------------------------------------------------------------------

FAILURE_THRESHOLD = 3          # consecutive failures to open the circuit
RECOVERY_TIMEOUT = 30          # seconds before trying again (half-open)

_cb_state = "CLOSED"
_cb_failures = 0
_cb_opened_at = 0


def _cb_record_success():
    global _cb_state, _cb_failures
    _cb_failures = 0
    _cb_state = "CLOSED"


def _cb_record_failure():
    global _cb_state, _cb_failures, _cb_opened_at
    _cb_failures += 1
    if _cb_failures >= FAILURE_THRESHOLD:
        _cb_state = "OPEN"
        _cb_opened_at = time.time()


def _cb_allow_request():
    global _cb_state
    if _cb_state == "CLOSED":
        return True
    if _cb_state == "OPEN" and time.time() - _cb_opened_at >= RECOVERY_TIMEOUT:
        _cb_state = "HALF_OPEN"
        return True
    return False


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def handler(event, context):
    detail = event.get("detail", {})
    enriched = enrich_raw(detail)

    # Firehose always receives the event — this is our durable path
    firehose.put_record(
        DeliveryStreamName=FIREHOSE_STREAM,
        Record={"Data": json.dumps(enriched) + "\n"},
    )

    # DynamoDB write protected by circuit breaker
    dynamo_ok = _write_to_dynamodb(enriched)

    emit_metric(detail, dynamo_ok)

    return {"statusCode": 200, "event_id": detail.get("event_id"), "dynamo_circuit": _cb_state}


def _write_to_dynamodb(enriched):
    if not _cb_allow_request():
        print(f"[CircuitBreaker] OPEN — skipping DynamoDB write (retry in {RECOVERY_TIMEOUT}s)")
        return False
    try:
        dynamo_record = json.loads(json.dumps(enriched), parse_float=Decimal)
        table.put_item(Item=dynamo_record)
        _cb_record_success()
        return True
    except Exception as e:
        _cb_record_failure()
        print(f"[CircuitBreaker] DynamoDB write failed ({_cb_failures}/{FAILURE_THRESHOLD}): {e}")
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def enrich_raw(record):
    record["processed_at"] = datetime.now(timezone.utc).isoformat()
    record["ttl"] = int(datetime.now(timezone.utc).timestamp()) + 86400
    return record


def emit_metric(record, dynamo_ok):
    event_type = record.get("event_type", "unknown")
    metrics = [
        {
            "MetricName": "EventCount",
            "Dimensions": [{"Name": "EventType", "Value": event_type}],
            "Value": 1,
            "Unit": "Count",
        }
    ]

    if event_type == "purchase":
        metrics.append(
            {
                "MetricName": "Revenue",
                "Dimensions": [{"Name": "Currency", "Value": record.get("currency", "USD")}],
                "Value": float(record.get("total_amount", 0)),
                "Unit": "None",
            }
        )

    # Circuit breaker observability — key metric for the demo
    metrics.append(
        {
            "MetricName": "DynamoCircuitOpen",
            "Value": 0 if dynamo_ok else 1,
            "Unit": "Count",
        }
    )

    cloudwatch.put_metric_data(Namespace="Ecommerce/Events", MetricData=metrics)
