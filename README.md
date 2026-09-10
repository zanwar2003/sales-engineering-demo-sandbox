# Sales Engineering Demo Sandbox

A small webhook receiver + client simulation â the kind of proof-of-concept a sales/solutions
engineer builds to show a prospective customer exactly how their system would integrate with
ours, live on a screen-share, without needing their real CRM connected to a sandbox account.

`client_demo.py` plays the part of the customer's CRM, sending signed webhook events for a few
realistic scenarios (a new contact, a won deal, a lost deal, an event type we don't route yet),
and `webhook_receiver.py` plays the part of our integration endpoint: verifying the signature,
routing the event, and logging it so you can show a prospect the event actually landed.

## Why this shape

Signature verification (HMAC-SHA256 over a shared secret, sent in a header) is the same pattern
used by Stripe, GitHub, and most serious webhook providers, so it demonstrates something that
transfers directly to a real integration conversation rather than a toy that only works in this
repo. The demo also deliberately sends one request with a bad signature, to show the receiver
correctly rejecting it â a common, reasonable question from a security-conscious technical
buyer.

## Running the demo

Terminal 1 â start the receiver:

```bash
pip install -r requirements.txt
python webhook_receiver.py
```

Terminal 2 â run the simulated customer CRM:

```bash
python client_demo.py
```

Expected output:

```
Simulating a customer CRM sending webhook events...

-> sent contact.created      status=200 body={'routed_to': 'sync_new_contact', 'status': 'accepted'}
-> sent contact.updated      status=200 body={'routed_to': 'update_contact_record', 'status': 'accepted'}
-> sent deal.won             status=200 body={'routed_to': 'trigger_onboarding_workflow', 'status': 'accepted'}
-> sent deal.lost            status=200 body={'routed_to': 'log_lost_reason', 'status': 'accepted'}
-> sent invoice.paid         status=200 body={'routed_to': 'unrouted_event_logged', 'status': 'accepted'}

Now demonstrating signature verification rejecting a tampered request:
-> sent contact.created      (bad signature) status=401 body={'error': 'invalid signature'}
```

You can also hit `GET /webhooks/events` on the receiver at any point during the demo to show the
event log building up live, and `GET /healthz` as a quick sanity check before a call.

## Running the tests

```bash
pip install -r requirements.txt
pytest tests/
```

## Project structure

```
webhook_receiver.py    # Flask endpoint: signature verification, event routing, in-memory log
client_demo.py          # simulates the customer's system sending signed events
tests/test_webhook.py   # signature verification, routing logic, and endpoint behavior
```

## Adapting this to a real integration

Swap `WEBHOOK_SECRET` for a per-customer secret pulled from a secrets manager at request time
(looked up by a customer ID in the request, rather than a single shared constant), and swap
`_route_event`'s stubbed actions for real downstream calls â the signature-verification and
routing shape stays the same either way.
