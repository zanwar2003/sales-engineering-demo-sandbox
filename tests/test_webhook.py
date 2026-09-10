import hashlib
import hmac
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from webhook_receiver import app, WEBHOOK_SECRET, verify_signature, _route_event  # noqa: E402


def sign(payload: bytes) -> str:
    return hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def test_verify_signature_accepts_correct_signature():
    payload = b'{"type": "contact.created"}'
    assert verify_signature(payload, sign(payload)) is True


def test_verify_signature_rejects_wrong_signature():
    payload = b'{"type": "contact.created"}'
    assert verify_signature(payload, "wrong-signature") is False


def test_verify_signature_rejects_missing_signature():
    assert verify_signature(b"{}", None) is False


def test_route_event_known_type():
    assert _route_event("deal.won", {}) == "trigger_onboarding_workflow"


def test_route_event_unknown_type_falls_back():
    assert _route_event("something.new", {}) == "unrouted_event_logged"


def test_webhook_endpoint_accepts_signed_request():
    client = app.test_client()
    event = {"type": "contact.created", "contact_id": "c_1"}
    payload = json.dumps(event).encode()
    resp = client.post(
        "/webhooks/crm",
        data=payload,
        headers={"Content-Type": "application/json", "X-Signature-256": sign(payload)},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "accepted"


def test_webhook_endpoint_rejects_unsigned_request():
    client = app.test_client()
    event = {"type": "contact.created"}
    resp = client.post("/webhooks/crm", json=event)
    assert resp.status_code == 401


def test_events_log_endpoint_returns_list():
    client = app.test_client()
    resp = client.get("/webhooks/events")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)
