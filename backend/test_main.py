import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    """Context manager fixture that handles startup/shutdown events."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def auth_headers(client):
    """Registers a test user and returns valid JWT Authorization headers."""
    # 1. Register a temporary user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "tester",
            "email": "tester@example.com",
            "password": "password123"
        }
    )
    
    # 2. Authenticate to get access token
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "tester",
            "password": "password123"
        }
    )
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# --- Tests ---

def test_get_metrics(client):
    """Public route - requires no auth."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200

def test_get_tickers(client, auth_headers):
    response = client.get("/api/v1/tickers", headers=auth_headers)
    print("\nDEBUG ERROR:", response.json())  # <--- Add this
    assert response.status_code == 200

def test_get_tickers_unauthorized(client):
    """Ensures unauthenticated requests are properly rejected."""
    response = client.get("/api/v1/tickers")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_get_chart_valid_ticker(client, auth_headers):
    response = client.get("/api/v1/chart/MTNCOM", headers=auth_headers)
    assert response.status_code == 200

def test_get_chart_invalid_ticker(client, auth_headers):
    response = client.get("/api/v1/chart/NONEXISTENT", headers=auth_headers)
    assert response.status_code == 404


