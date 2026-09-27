"""Tests verifying that Operator Authentication protects all telemetry routes."""

import pytest

def test_unauthenticated_request_is_denied(client):
    # Overwrite authorization header to empty
    res = client.get("/overview", headers={"Authorization": ""})
    assert res.status_code == 401
    assert "Restricted access" in res.json().get("detail", "")

def test_invalid_operator_token_is_denied(client):
    res = client.get("/overview", headers={"Authorization": "Bearer invalid-wrong-token"})
    assert res.status_code == 401

def test_login_with_wrong_key_fails(client):
    res = client.post("/auth/login", json={"key": "wrong-key"})
    assert res.status_code == 401
    assert "Invalid passkey" in res.json().get("detail", "")

def test_login_with_correct_key_succeeds_and_unlocks(client):
    res = client.post("/auth/login", json={"key": "atanu-telemetry-2026"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["operator"]["name"] == "Atanu"

    # Use received token to access overview
    token = data["token"]
    overview_res = client.get("/overview", headers={"Authorization": f"Bearer {token}"})
    assert overview_res.status_code == 200
    assert "metrics" in overview_res.json()

def test_public_health_endpoint_is_accessible_without_auth(client):
    res = client.get("/health", headers={"Authorization": ""})
    assert res.status_code == 200
    assert res.json().get("status") == "ok"
