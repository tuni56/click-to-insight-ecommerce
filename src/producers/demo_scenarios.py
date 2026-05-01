import json
import time
import uuid
import random
import sys
import os
import base64
import boto3
from datetime import datetime, timezone
from confluent_kafka import Producer

BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
SASL_USERNAME = os.environ["KAFKA_API_KEY"]
SASL_PASSWORD = os.environ["KAFKA_API_SECRET"]
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-2")
LAMBDA_FUNCTION = "click-to-insight-process-event"

producer = Producer({
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": "PLAIN",
    "sasl.username": SASL_USERNAME,
    "sasl.password": SASL_PASSWORD,
})
lambda_client = boto3.client("lambda", region_name=REGION)
USERS = [f"user_{i}" for i in range(1, 51)]
PAGES = ["/home", "/products", "/products/123", "/products/456", "/cart", "/checkout", "/checkout/success"]
PRODUCTS = [
    {"id": "prod_100", "name": "Wireless Headphones", "price": 59.99},
    {"id": "prod_101", "name": "USB-C Hub", "price": 34.99},
    {"id": "prod_102", "name": "Mechanical Keyboard", "price": 129.99},
    {"id": "prod_103", "name": "Monitor Stand", "price": 45.00},
    {"id": "prod_104", "name": "Webcam HD", "price": 79.99},
    {"id": "prod_105", "name": "Laptop Sleeve", "price": 24.99},
]

SCENARIOS = {
    "normal": {
        "description": "Normal traffic — steady e-commerce flow",
        "page_views": 5, "cart_events": 3, "purchases": 1,
        "delay": 1.0, "users": 20,
    },
    "blackfriday": {
        "description": "🔥 Black Friday spike — 5x traffic burst",
        "page_views": 25, "cart_events": 15, "purchases": 5,
        "delay": 0.2, "users": 50,
    },
    "checkout_drop": {
        "description": "⚠️ Checkout drop — lots of views, few purchases",
        "page_views": 20, "cart_events": 10, "purchases": 0,
        "delay": 0.5, "users": 30,
    },
    "dlq_poison": {
        "description": "💀 Poison pills — events that simulate Lambda failures → DLQ",
        "count": 5,
        "delay": 0.5,
    },
}


def page_view(users):
    return {
        "event_type": "page_view",
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(users),
        "page_url": random.choice(PAGES),
        "session_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def cart_event(users):
    product = random.choice(PRODUCTS)
    return {
        "event_type": "cart_event",
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(users),
        "product_id": product["id"],
        "product_name": product["name"],
        "action": random.choice(["add", "remove"]),
        "quantity": random.randint(1, 3),
        "unit_price": product["price"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def purchase_event(users):
    items = random.sample(PRODUCTS, k=random.randint(1, 3))
    order_items = [
        {"product_id": p["id"], "product_name": p["name"],
         "quantity": random.randint(1, 2), "unit_price": p["price"]}
        for p in items
    ]
    total = sum(i["unit_price"] * i["quantity"] for i in order_items)
    return {
        "event_type": "purchase",
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(users),
        "order_id": str(uuid.uuid4()),
        "items": order_items,
        "total_amount": round(total, 2),
        "currency": "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def delivery_report(err, msg):
    if err:
        print(f"  ⚠ Delivery failed [{msg.topic()}]: {err}")


def invoke_lambda(batch_by_topic):
    records = {
        f"{topic}-0": [{"value": base64.b64encode(json.dumps(e).encode()).decode()} for e in events]
        for topic, events in batch_by_topic.items() if events
    }
    lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION,
        InvocationType="Event",
        Payload=json.dumps({"records": records}),
    )


def run_dlq_scenario():
    scenario = SCENARIOS["dlq_poison"]
    sqs = boto3.client("sqs", region_name=REGION)
    queue_name = "click-to-insight-dlq"
    try:
        queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
    except Exception as e:
        print(f"  ❌ Could not find DLQ '{queue_name}': {e}")
        return 0

    print(f"\n{'='*60}")
    print(f"  SCENARIO: DLQ_POISON")
    print(f"  {scenario['description']}")
    print(f"{'='*60}\n")

    total = 0
    for i in range(scenario["count"]):
        poison = {
            "error": "Simulated Lambda failure",
            "original_event": {
                "event_type": random.choice(["page_view", "cart_event", "purchase"]),
                "event_id": str(uuid.uuid4()),
                "user_id": random.choice(USERS[:10]),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "failure_reason": random.choice([
                "DynamoDB ProvisionedThroughputExceededException",
                "Firehose ServiceUnavailableException",
                "Lambda timeout after 30s",
                "ValidationError: missing required field 'event_type'",
            ]),
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "retry_count": 3,
        }
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(poison))
        total += 1
        print(f"  💀 [{i+1}/{scenario['count']}] Poison pill → DLQ  reason={poison['failure_reason']}")
        time.sleep(scenario["delay"])

    print(f"\n✅ Sent {total} poison pills to DLQ '{queue_name}'")
    return total


def run_scenario(name, duration_seconds=30):
    if name == "dlq_poison":
        return run_dlq_scenario()

    scenario = SCENARIOS[name]
    users = USERS[: scenario["users"]]
    delay = scenario["delay"]

    print(f"\n{'='*60}")
    print(f"  SCENARIO: {name.upper()}")
    print(f"  {scenario['description']}")
    print(f"  Duration: {duration_seconds}s | Delay: {delay}s")
    print(f"{'='*60}\n")

    total = 0
    start = time.time()

    while time.time() - start < duration_seconds:
        builders = [
            (page_view, "page_view", scenario["page_views"]),
            (cart_event, "cart_event", scenario["cart_events"]),
            (purchase_event, "purchase", scenario["purchases"]),
        ]
        batch_count = 0
        batch_by_topic = {"page_view": [], "cart_event": [], "purchase": []}
        for builder, topic, count in builders:
            for _ in range(count):
                event = builder(users)
                batch_by_topic[topic].append(event)
                producer.produce(
                    topic=topic,
                    key=event["user_id"],
                    value=json.dumps(event),
                    callback=delivery_report,
                )
                batch_count += 1

        producer.flush()
        invoke_lambda(batch_by_topic)
        total += batch_count
        elapsed = int(time.time() - start)
        print(f"  [{elapsed:3d}s] sent {batch_count} events (total: {total})")
        time.sleep(delay)

    print(f"\n✅ Scenario '{name}' complete — {total} events in {duration_seconds}s")
    return total


def main():
    print("🎬 ACM Week 2026 — Demo: Del Click al Insight")
    print("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] in SCENARIOS:
        run_scenario(sys.argv[1], duration_seconds=int(sys.argv[2]) if len(sys.argv) > 2 else 30)
        return

    print("\nThis script runs 3 scenarios to show different traffic patterns:\n")
    for name, s in SCENARIOS.items():
        print(f"  {name:15s} — {s['description']}")

    print("\n▶ Starting in 3 seconds... (Ctrl+C to stop)\n")
    time.sleep(3)

    grand_total = 0

    grand_total += run_scenario("normal", duration_seconds=20)
    print("\n⏳ Transitioning to Black Friday...\n")
    time.sleep(2)

    grand_total += run_scenario("blackfriday", duration_seconds=20)
    print("\n⏳ Something is wrong with checkout...\n")
    time.sleep(2)

    grand_total += run_scenario("checkout_drop", duration_seconds=15)

    print("\n⏳ Simulating failed events hitting the DLQ...\n")
    time.sleep(2)
    grand_total += run_scenario("dlq_poison")

    print(f"\n{'='*60}")
    print(f"  🎬 DEMO COMPLETE — {grand_total} total events sent")
    print(f"  Now check Grafana Dashboard, DLQ, and Athena queries!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
