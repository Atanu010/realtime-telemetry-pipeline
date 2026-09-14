"""Criterion: Operators can acknowledge and resolve alerts.

The seeded alert-lag row is the row the UI acceptance flow exercises end-to-end
(acknowledge -> resolve via the browser check `alerts-acknowledge-and-resolve`).
To avoid two artifacts racing to mutate the same singleton seeded row, this
backend test stays read-only on alert-lag (verifies seed shape) and covers the
API validation rule (resolve requires a note) against a different alert id.
"""


def test_alert_lag_seed_shape_is_active_with_expected_fields(client):
    listing = client.get("/alerts")
    assert listing.status_code == 200
    alerts = {a["id"]: a for a in listing.json()}
    assert "alert-lag" in alerts
    seed = alerts["alert-lag"]
    assert seed["status"] == "active", f"expected alert-lag seeded active, got {seed['status']}"
    assert seed["severity"] == "P1"
    assert seed["acknowledged_at"] is None
    assert seed["resolved_at"] is None


def test_resolve_requires_a_note(client):
    # alert-latency is already resolved in the seed; resolving again with an empty
    # note must still be rejected by validation before any state check runs.
    resp = client.post("/alerts/alert-latency/resolve", json={"resolution_note": ""})
    assert resp.status_code == 422
