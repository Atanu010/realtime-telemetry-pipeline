"""Criterion: Operators can manage pipeline resources (create a source via API)."""
import uuid


def test_create_source_pipeline_is_persisted(client):
    name = f"tscheck-source-{uuid.uuid4().hex[:8]}"
    payload = {"name": name, "kind": "source", "protocol": "Kafka", "partitions": 5, "retention_days": 10}

    resp = client.post("/pipelines", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == name
    assert body["kind"] == "source"
    assert body["protocol"] == "Kafka"
    assert body["partitions"] == 5
    assert body["retention_days"] == 10
    new_id = body["id"]

    listing = client.get("/pipelines")
    assert listing.status_code == 200
    ids = [p["id"] for p in listing.json()]
    assert new_id in ids


def test_create_pipeline_rejects_invalid_protocol(client):
    name = f"tscheck-source-bad-{uuid.uuid4().hex[:8]}"
    resp = client.post("/pipelines", json={"name": name, "kind": "source", "protocol": "NotAProtocol"})
    assert resp.status_code == 422
