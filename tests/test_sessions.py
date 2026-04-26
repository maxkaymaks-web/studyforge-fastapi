from fastapi.testclient import TestClient


def auth_headers(client: TestClient, email: str, role: str = "student") -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={
            "full_name": email.split("@")[0],
            "email": email,
            "password": "supersecure123",
            "role": role,
        },
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "supersecure123"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_topic(client: TestClient, headers: dict[str, str]) -> int:
    course_response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Probability",
            "description": "Probability theory",
            "exam_date": "2026-06-20",
            "target_score": 90,
            "weekly_hours_goal": 7,
            "color_theme": "mint",
        },
    )
    course_id = course_response.json()["id"]
    topic_response = client.post(
        "/api/topics",
        headers=headers,
        json={
            "course_id": course_id,
            "title": "Bayes Rule",
            "description": "Conditional probability",
            "difficulty": 4,
            "importance": 5,
            "estimated_minutes": 110,
            "mastery_level": 10,
            "status": "planned",
        },
    )
    return topic_response.json()["id"]


def test_session_crud_flow(client: TestClient) -> None:
    headers = auth_headers(client, "ada@example.com")
    topic_id = create_topic(client, headers)

    create_response = client.post(
        "/api/sessions",
        headers=headers,
        json={
            "topic_id": topic_id,
            "planned_for": "2026-05-01",
            "actual_minutes": 90,
            "focus_score": 8,
            "notes": "Good concentration",
        },
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    list_response = client.get(f"/api/sessions?topic_id={topic_id}", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/sessions/{session_id}", headers=headers)
    assert detail_response.status_code == 200

    update_response = client.put(
        f"/api/sessions/{session_id}",
        headers=headers,
        json={
            "planned_for": "2026-05-02",
            "actual_minutes": 100,
            "focus_score": 9,
            "notes": "Even better concentration",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["focus_score"] == 9

    delete_response = client.delete(f"/api/sessions/{session_id}", headers=headers)
    assert delete_response.status_code == 204


def test_session_requires_owned_topic(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner@example.com")
    outsider_headers = auth_headers(client, "outsider@example.com")
    topic_id = create_topic(client, owner_headers)

    response = client.post(
        "/api/sessions",
        headers=outsider_headers,
        json={
            "topic_id": topic_id,
            "planned_for": "2026-05-01",
            "actual_minutes": 50,
            "focus_score": 6,
            "notes": "Blocked",
        },
    )
    assert response.status_code == 404
