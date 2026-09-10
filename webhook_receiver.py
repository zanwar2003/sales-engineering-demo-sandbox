"""
A small webhook receiver + client demo, the kind of proof-of-concept a sales/solutions engineer
builds to show a prospective customer how their system would integrate with ours during a demo
or technical evaluation call.

Endpoint:
    POST /webhooks/crm  -- receives a signed event from a (simulated) customer CRM, verifies the
                            HMAC signature, and routes it based on event type.

Signature verification uses the same HMAC-SHA256 "shared secret in a header" pattern used by
Stripe, GitHub, and most webhook providers, so the pattern transfers directly to a real
integration.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

# In a real integration this would be a per-customer secret issued at onboarding time and stored
# in a secrets manager, not hardcoded. Kept as a module-level constant here for a self-contained
# demo â client_demo.py imports the same constant to sign its sample requests.
WEBHOOK_SECRET = "demo-shared-secret-not-for-production"

# In-memory event log so the demo has something to show back (`GET /webhooks/events`) without
# needing a database.
_received_events: list[dict] = []


def verify_signature(payload: bytes, signature_header: str | None) -> bool:
    if not signature_header:
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    # Constant-time comparison to avoid leaking the correct signature one byte at a time via
    # response-time side channels.
    return hmac.compare_digest(expected, signature_header)


@app.post("/webhooks/crm")
def receive_crm_webhook():
    signature = request.headers.get("X-Signature-256")
    if not verify_signature(request.get_data(), signature):
        return jsonify({"error": "invalid signature"}), 401

    event = request.get_json(silent=True) or {}
    event_type = event.get("type", "unknown")

    result = _route_event(event_type, event)
    _received_events.append({"received_at": time.time(), "type": event_type, "result": result})

    return jsonify({"status": "accepted", "routed_to": result}), 200


def _route_event(event_type: str, event: dict) -> str:
    """Simulates routing a webhook event to the right downstream action for a demo integration."""
    routes = {
        "contact.created": "sync_new_contact",
        "contact.updated": "update_contact_record",
        "deal.won": "trigger_onboarding_workflow",
        "deal.lost": "log_lost_reason",
    }
    return routes.get(event_type, "unrouted_event_logged")


@app.get("/webhooks/events")
def list_events():
    """Lets the demo show what's been received so far, most recent first."""
    return jsonify(list(reversed(_received_events)))


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5002)
