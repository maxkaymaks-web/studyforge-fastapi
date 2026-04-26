from fastapi.testclient import TestClient

from app.index import app


def test_vercel_entrypoint_exposes_health() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
