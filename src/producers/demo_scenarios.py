import json
import time
import uuid
import random
import sys
import boto3
from datetime import datetime, timezone

REGION = "us-east-2"
EVENT_BUS = "click-to-insight-events"
SOURCE = "ecommerce.storefront"

client = boto3.client("events", region_name=REGION)

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


def send_batch(entries):
    # EventBridge accepts max 10 entries per put_events call
    failed = 0
    for i in range(0, len(entries), 10):
        resp = client.put_events(Entries=entries[i:i + 10])
        failed += resp.get("FailedEntryCount", 0)
    return failed


def run_scenario(name, duration_seconds=30):
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
        entries = []
        builders = [
            (page_view, "page_view", scenario["page_views"]),
            (cart_event, "cart_event", scenario["cart_events"]),
            (purchase_event, "purchase", scenario["purchases"]),
        ]
        for builder, detail_type, count in builders:
            for _ in range(count):
                event = builder(users)
                entries.append({
                    "Source": SOURCE,
                    "DetailType": detail_type,
                    "Detail": json.dumps(event),
                    "EventBusName": EVENT_BUS,
                })

        failed = send_batch(entries)
        total += len(entries)
        elapsed = int(time.time() - start)
        status = f"  [{elapsed:3d}s] sent {len(entries)} events (total: {total})"
        if failed:
            status += f" ⚠ {failed} failed"
        print(status)
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

    # Act 1: Normal traffic
    grand_total += run_scenario("normal", duration_seconds=20)
    print("\n⏳ Transitioning to Black Friday...\n")
    time.sleep(2)

    # Act 2: Black Friday spike
    grand_total += run_scenario("blackfriday", duration_seconds=20)
    print("\n⏳ Something is wrong with checkout...\n")
    time.sleep(2)

    # Act 3: Checkout drop
    grand_total += run_scenario("checkout_drop", duration_seconds=15)

    print(f"\n{'='*60}")
    print(f"  🎬 DEMO COMPLETE — {grand_total} total events sent")
    print(f"  Now check CloudWatch Dashboard and Athena queries!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
