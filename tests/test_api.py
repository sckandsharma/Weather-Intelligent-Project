from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    assert "Welcome to" in res.json()["message"]


def test_health_endpoints(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_db = client.get("/health/database")
    assert res_db.status_code == 200
    assert res_db.json()["status"] == "healthy"
