import json
import time
import uuid
import random
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

USERS = [f"user_{i}" for i in range(1, 21)]
PAGES = ["/home", "/products", "/products/123", "/cart", "/checkout", "/checkout/success"]
PRODUCTS = [
    {"id": "prod_100", "name": "Wireless Headphones", "price": 59.99},
    {"id": "prod_101", "name": "USB-C Hub", "price": 34.99},
    {"id": "prod_102", "name": "Mechanical Keyboard", "price": 129.99},
    {"id": "prod_103", "name": "Monitor Stand", "price": 45.00},
    {"id": "prod_104", "name": "Webcam HD", "price": 79.99},
    {"id": "prod_105", "name": "Laptop Sleeve", "price": 24.99},
]

EVENTS = [
    (None, "page_view", 5),
    (None, "cart_event", 3),
    (None, "purchase", 1),
]


def page_view():
    return {
        "event_type": "page_view",
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(USERS),
        "page_url": random.choice(PAGES),
        "session_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def cart_event():
    product = random.choice(PRODUCTS)
    return {
        "event_type": "cart_event",
        "event_id": str(uuid.uuid4()),
        "user_id": random.choice(USERS),
        "product_id": product["id"],
        "product_name": product["name"],
        "action": random.choice(["add", "remove"]),
        "quantity": random.randint(1, 3),
        "unit_price": product["price"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def purchase_event():
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
        "user_id": random.choice(USERS),
        "order_id": str(uuid.uuid4()),
        "items": order_items,
        "total_amount": round(total, 2),
        "currency": "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


BUILDERS = {"page_view": page_view, "cart_event": cart_event, "purchase": purchase_event}


def invoke_lambda(batch_by_topic):
    """Invoke Lambda with a Kafka-shaped payload so the pipeline runs end-to-end."""
    records = {
        f"{topic}-0": [{"value": base64.b64encode(json.dumps(e).encode()).decode()} for e in events]
        for topic, events in batch_by_topic.items() if events
    }
    lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION,
        InvocationType="Event",  # async — don't block the producer
        Payload=json.dumps({"records": records}),
    )


def delivery_report(err, msg):
    if err:
        print(f"  ⚠ Delivery failed: {err}", flush=True)


print("🚀 Producing events to Kafka (Confluent Cloud) → Lambda → Grafana", flush=True)
print("   Ctrl+C to stop\n", flush=True)

total_sent = 0
try:
    while True:
        batch_by_topic = {"page_view": [], "cart_event": [], "purchase": []}
        for _, topic, weight in EVENTS:
            builder = BUILDERS[topic]
            for _ in range(weight):
                event = builder()
                batch_by_topic[topic].append(event)
                producer.produce(
                    topic=topic,
                    key=event["user_id"],
                    value=json.dumps(event),
                    callback=delivery_report,
                )
                print(f"  [{topic:<12}] user={event['user_id']:<8} id={event['event_id'][:8]}", flush=True)

        producer.flush()
        invoke_lambda(batch_by_topic)
        total_sent += sum(w for _, _, w in EVENTS)
        print(f"  --- batch sent ({total_sent} total) ---\n", flush=True)
        time.sleep(1)
except KeyboardInterrupt:
    producer.flush()
    print(f"\n✅ Producer stopped. Total events sent: {total_sent}")
