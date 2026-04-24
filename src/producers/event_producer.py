import json
import time
import uuid
import random
import boto3
from datetime import datetime, timezone

REGION = "us-east-2"
EVENT_BUS = "click-to-insight-events"
SOURCE = "ecommerce.storefront"

client = boto3.client("events", region_name=REGION)

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
        {
            "product_id": p["id"],
            "product_name": p["name"],
            "quantity": random.randint(1, 2),
            "unit_price": p["price"],
        }
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


# Weighted distribution: many page views, some cart events, few purchases
EVENTS = [
    (page_view, "page_view", 5),
    (cart_event, "cart_event", 3),
    (purchase_event, "purchase", 1),
]


def send_batch(entries):
    response = client.put_events(Entries=entries)
    failed = response.get("FailedEntryCount", 0)
    if failed:
        print(f"  ⚠ {failed} events failed")
    return failed


print(f"🚀 Producing events to EventBridge bus '{EVENT_BUS}' in {REGION}")
print("   Ctrl+C to stop\n")

total_sent = 0
try:
    while True:
        entries = []
        for builder, detail_type, weight in EVENTS:
            for _ in range(weight):
                event = builder()
                entries.append(
                    {
                        "Source": SOURCE,
                        "DetailType": detail_type,
                        "Detail": json.dumps(event),
                        "EventBusName": EVENT_BUS,
                    }
                )
                print(f"  [{detail_type:<12}] user={event['user_id']:<8} id={event['event_id'][:8]}")

        send_batch(entries)
        total_sent += len(entries)
        print(f"  --- batch sent ({total_sent} total) ---\n")
        time.sleep(1)
except KeyboardInterrupt:
    print(f"\n✅ Producer stopped. Total events sent: {total_sent}")
