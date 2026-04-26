from fastapi.testclient import TestClient


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={
            "full_name": email.split("@")[0],
            "email": email,
            "password": "supersecure123",
            "role": "student",
        },
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "supersecure123"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_course(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Algorithms",
            "description": "Core algorithms course",
            "exam_date": "2026-06-15",
            "target_score": 92,
            "weekly_hours_goal": 9,
            "color_theme": "violet",
        },
    )
    return response.json()["id"]


def test_topic_crud_flow(client: TestClient) -> None:
    headers = auth_headers(client, "ada@example.com")
    course_id = create_course(client, headers)

    create_response = client.post(
        "/api/topics",
        headers=headers,
        json={
            "course_id": course_id,
            "title": "Dynamic Programming",
            "description": "State transition basics",
            "difficulty": 5,
            "importance": 5,
            "estimated_minutes": 140,
            "mastery_level": 10,
            "status": "planned",
        },
    )
    assert create_response.status_code == 201
    topic_id = create_response.json()["id"]

    list_response = client.get(f"/api/topics?course_id={course_id}", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/topics/{topic_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Dynamic Programming"

    update_response = client.put(
        f"/api/topics/{topic_id}",
        headers=headers,
        json={
            "title": "Dynamic Programming",
            "description": "State transitions and knapsack",
            "difficulty": 5,
            "importance": 5,
            "estimated_minutes": 150,
            "mastery_level": 55,
            "status": "in_progress",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["mastery_level"] == 55

    delete_response = client.delete(f"/api/topics/{topic_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/topics/{topic_id}", headers=headers)
    assert missing_response.status_code == 404


def test_topic_creation_requires_owned_course(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner@example.com")
    outsider_headers = auth_headers(client, "outsider@example.com")
    course_id = create_course(client, owner_headers)

    response = client.post(
        "/api/topics",
        headers=outsider_headers,
        json={
            "course_id": course_id,
            "title": "Graphs",
            "description": "Shortest path algorithms",
            "difficulty": 4,
            "importance": 4,
            "estimated_minutes": 120,
            "mastery_level": 15,
            "status": "planned",
        },
    )
    assert response.status_code == 404
