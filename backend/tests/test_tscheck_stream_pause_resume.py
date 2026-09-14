"""Criterion: Operators can pause and resume the stream safely."""


def test_pause_then_resume_stream(client):
    pause_resp = client.post("/stream/pause")
    assert pause_resp.status_code == 200, pause_resp.text
    paused = pause_resp.json()
    assert paused["status"] == "paused"

    state_resp = client.get("/stream")
    assert state_resp.status_code == 200
    assert state_resp.json()["status"] == "paused"

    resume_resp = client.post("/stream/resume")
    assert resume_resp.status_code == 200, resume_resp.text
    resumed = resume_resp.json()
    assert resumed["status"] == "running"

    state_resp2 = client.get("/stream")
    assert state_resp2.status_code == 200
    assert state_resp2.json()["status"] == "running"
