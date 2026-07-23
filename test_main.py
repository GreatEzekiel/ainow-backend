import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "tester", "email": "tester@example.com", "password": "password123"}
    )
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "tester", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_metrics(client):
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200

def test_get_tickers_unauthorized(client):
    response = client.get("/api/v1/tickers")
    assert response.status_code == 401

def test_get_tickers_authorized(client, auth_headers):
    response = client.get("/api/v1/tickers", headers=auth_headers)
    assert response.status_code == 200