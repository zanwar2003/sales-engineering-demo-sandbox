"""
Simulates a customer's CRM sending signed webhook events to our receiver â the kind of live
walkthrough script a sales engineer runs on a screen-share to show a prospect exactly what their
integration would look like end-to-end, without needing their real CRM connected.

Usage (with webhook_receiver.py running separately on port 5002):
    python client_demo.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import requests

from webhook_receiver import WEBHOOK_SECRET

RECEIVER_URL = "http://localhost:5002/webhooks/crm"

DEMO_EVENTS = [
    {"type": "contact.created", "contact_id": "c_1001", "name": "Jordan Ellis"},
    {"type": "contact.updated", "contact_id": "c_1001", "field": "email"},
    {"type": "deal.won", "deal_id": "d_4471", "amount": 48000},
    {"type": "deal.lost", "deal_id": "d_4472", "reason": "went with a competitor"},
    {"type": "invoice.paid", "invoice_id": "i_889"},  # deliberately an event type we don't route
]


def sign(payload: bytes) -> str:
    return hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def send_event(event: dict) -> None:
    payload = json.dumps(event).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": sign(payload),
    }
    response = requests.post(RECEIVER_URL, data=payload, headers=headers, timeout=5)
    print(f"-> sent {event['type']:20s} status={response.status_code} body={response.json()}")


def send_event_with_bad_signature(event: dict) -> None:
    """Demonstrates the receiver correctly rejecting a tampered/unsigned request."""
    payload = json.dumps(event).encode()
    headers = {"Content-Type": "application/json", "X-Signature-256": "not-a-real-signature"}
    response = requests.post(RECEIVER_URL, data=payload, headers=headers, timeout=5)
    print(f"-> sent {event['type']:20s} (bad signature) status={response.status_code} body={response.json()}")


def main() -> None:
    print("Simulating a customer CRM sending webhook events...\n")
    for event in DEMO_EVENTS:
        send_event(event)
        time.sleep(0.2)

    print("\nNow demonstrating signature verification rejecting a tampered request:")
    send_event_with_bad_signature({"type": "contact.created", "contact_id": "c_fake"})


if __name__ == "__main__":
    main()
