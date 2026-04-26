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


def test_course_crud_flow(client: TestClient) -> None:
    headers = auth_headers(client, "ada@example.com")
    create_response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Linear Algebra",
            "description": "Matrices and vectors",
            "exam_date": "2026-06-01",
            "target_score": 95,
            "weekly_hours_goal": 8,
            "color_theme": "emerald",
        },
    )
    assert create_response.status_code == 201
    course_id = create_response.json()["id"]

    list_response = client.get("/api/courses", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/api/courses/{course_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Linear Algebra"

    update_response = client.put(
        f"/api/courses/{course_id}",
        headers=headers,
        json={
            "title": "Advanced Linear Algebra",
            "description": "Matrices, vectors, and eigenvalues",
            "exam_date": "2026-06-10",
            "target_score": 97,
            "weekly_hours_goal": 10,
            "color_theme": "ocean",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["target_score"] == 97

    delete_response = client.delete(f"/api/courses/{course_id}", headers=headers)
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/courses/{course_id}", headers=headers)
    assert missing_response.status_code == 404


def test_course_access_is_scoped_to_owner(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner@example.com")
    outsider_headers = auth_headers(client, "outsider@example.com")

    create_response = client.post(
        "/api/courses",
        headers=owner_headers,
        json={
            "title": "Physics",
            "description": "Mechanics",
            "exam_date": "2026-07-01",
            "target_score": 88,
            "weekly_hours_goal": 6,
            "color_theme": "amber",
        },
    )
    course_id = create_response.json()["id"]

    outsider_list = client.get("/api/courses", headers=outsider_headers)
    assert outsider_list.status_code == 200
    assert outsider_list.json() == []

    outsider_detail = client.get(f"/api/courses/{course_id}", headers=outsider_headers)
    assert outsider_detail.status_code == 404
