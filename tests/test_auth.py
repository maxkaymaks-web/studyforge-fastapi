from fastapi.testclient import TestClient


def test_register_user_returns_profile(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "supersecure123",
            "role": "student",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["role"] == "student"
    assert "id" in body


def test_register_duplicate_email_returns_400(client: TestClient) -> None:
    payload = {
        "full_name": "Ada Lovelace",
        "email": "ada@example.com",
        "password": "supersecure123",
        "role": "student",
    }
    first_response = client.post("/api/auth/register", json=payload)
    second_response = client.post("/api/auth/register", json=payload)
    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Email already registered"


def test_login_returns_access_token(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "supersecure123",
            "role": "student",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "supersecure123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "supersecure123",
            "role": "student",
        },
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "supersecure123"},
    )
    token = login_response.json()["access_token"]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["full_name"] == "Ada Lovelace"
