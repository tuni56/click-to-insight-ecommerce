import json
import os
from decimal import Decimal
import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-2"))
firehose = boto3.client("firehose", region_name=os.environ.get("AWS_REGION", "us-east-2"))
cloudwatch = boto3.client("cloudwatch", region_name=os.environ.get("AWS_REGION", "us-east-2"))

TABLE_NAME = os.environ.get("TABLE_NAME", "ecommerce-events")
FIREHOSE_STREAM = os.environ.get("FIREHOSE_STREAM", "ecommerce-events-to-s3")

table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    detail = event.get("detail", {})

    # Firehose gets the raw JSON (floats OK)
    firehose.put_record(
        DeliveryStreamName=FIREHOSE_STREAM,
        Record={"Data": json.dumps(enrich_raw(detail)) + "\n"},
    )

    # DynamoDB needs Decimal — re-parse with Decimal
    dynamo_record = json.loads(json.dumps(enrich_raw(detail)), parse_float=Decimal)
    table.put_item(Item=dynamo_record)

    emit_metric(detail)

    return {"statusCode": 200, "event_id": detail.get("event_id")}


def enrich_raw(record):
    record["processed_at"] = datetime.now(timezone.utc).isoformat()
    record["ttl"] = int(datetime.now(timezone.utc).timestamp()) + 86400
    return record


def emit_metric(record):
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

    cloudwatch.put_metric_data(Namespace="Ecommerce/Events", MetricData=metrics)
