"""Criterion: Operators can manage external connection profiles safely.

Kafka/Redis/TimescaleDB profiles are redacted placeholders (no real credentials);
testing one must clearly report mocked=True, ok=False rather than claiming a live
connection succeeded.
"""


def test_integrations_list_has_placeholder_profiles(client):
    resp = client.get("/integrations")
    assert resp.status_code == 200
    integrations = resp.json()
    kinds = {i["kind"] for i in integrations}
    assert {"kafka", "redis", "timescaledb"}.issubset(kinds)
    for integ in integrations:
        assert integ["credential_state"] == "placeholder"


def test_testing_a_placeholder_integration_reports_mocked_unavailable(client):
    resp = client.get("/integrations")
    timescale = next(i for i in resp.json() if i["kind"] == "timescaledb")

    test_resp = client.post(f"/integrations/{timescale['id']}/test")
    assert test_resp.status_code == 200, test_resp.text
    result = test_resp.json()
    assert result["mocked"] is True
    assert result["ok"] is False
    assert result["detail"]
