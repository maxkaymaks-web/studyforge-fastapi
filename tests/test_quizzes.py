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
            "title": "Statistics",
            "description": "Statistics course",
            "exam_date": "2026-06-25",
            "target_score": 91,
            "weekly_hours_goal": 6,
            "color_theme": "rose",
        },
    )
    course_id = course_response.json()["id"]
    topic_response = client.post(
        "/api/topics",
        headers=headers,
        json={
            "course_id": course_id,
            "title": "Normal Distribution",
            "description": "Core distribution properties",
            "difficulty": 4,
            "importance": 4,
            "estimated_minutes": 100,
            "mastery_level": 20,
            "status": "planned",
        },
    )
    return topic_response.json()["id"]


def test_quiz_attempt_crud_flow(client: TestClient) -> None:
    headers = auth_headers(client, "ada@example.com")
    topic_id = create_topic(client, headers)

    create_response = client.post(
        "/api/quizzes",
        headers=headers,
        json={"topic_id": topic_id, "score": 7, "max_score": 10},
    )
    assert create_response.status_code == 201
    attempt_id = create_response.json()["id"]

    list_response = client.get(f"/api/quizzes?topic_id={topic_id}", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/quizzes/{attempt_id}", headers=headers)
    assert detail_response.status_code == 200

    update_response = client.put(
        f"/api/quizzes/{attempt_id}",
        headers=headers,
        json={"score": 8, "max_score": 10},
    )
    assert update_response.status_code == 200
    assert update_response.json()["score"] == 8

    delete_response = client.delete(f"/api/quizzes/{attempt_id}", headers=headers)
    assert delete_response.status_code == 204


def test_quiz_attempt_requires_owned_topic(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner@example.com")
    outsider_headers = auth_headers(client, "outsider@example.com")
    topic_id = create_topic(client, owner_headers)

    response = client.post(
        "/api/quizzes",
        headers=outsider_headers,
        json={"topic_id": topic_id, "score": 5, "max_score": 10},
    )
    assert response.status_code == 404
