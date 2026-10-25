import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

import api  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "PANTRY_PATH", tmp_path / "pantry.json")
    return TestClient(api.app)


def test_health(client):
    assert client.get("/health").json()["ok"] is True


def test_pantry_round_trip(client):
    r = client.put("/pantry", json=["Eggs", "onion", "rice"])
    assert r.json()["size"] == 3
    assert client.get("/pantry").json()["items"] == ["eggs", "onion", "rice"]


def test_plan_week(client):
    client.put("/pantry", json={"items": ["eggs", "onion", "garlic", "rice", "salt", "pepper"]})
    r = client.post("/plan-week-server", json={"budget": 15, "max_time": 30, "strategy": "knapsack_max_recipes"})
    body = r.json()
    assert r.status_code == 200
    assert body["week_plan"] and body["metrics"]["total_spend"] <= 15


def test_bad_strategy_returns_422(client):
    assert client.post("/plan-week-server", json={"strategy": "nope"}).status_code == 422
