from fastapi.testclient import TestClient


def auth_headers(client: TestClient, email: str, role: str) -> dict[str, str]:
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


def create_course(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Machine Learning",
            "description": "ML theory",
            "exam_date": "2026-06-30",
            "target_score": 94,
            "weekly_hours_goal": 11,
            "color_theme": "indigo",
        },
    )
    return response.json()["id"]


def test_mentor_comment_flow(client: TestClient) -> None:
    student_headers = auth_headers(client, "student@example.com", "student")
    mentor_headers = auth_headers(client, "mentor@example.com", "mentor")
    course_id = create_course(client, student_headers)

    create_response = client.post(
        "/api/comments",
        headers=mentor_headers,
        json={"course_id": course_id, "body": "Review dynamic programming every 3 days."},
    )
    assert create_response.status_code == 201
    comment_id = create_response.json()["id"]

    list_response = client.get(f"/api/comments?course_id={course_id}", headers=student_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    delete_response = client.delete(f"/api/comments/{comment_id}", headers=mentor_headers)
    assert delete_response.status_code == 204


def test_student_cannot_create_mentor_comment(client: TestClient) -> None:
    student_headers = auth_headers(client, "student@example.com", "student")
    course_id = create_course(client, student_headers)

    response = client.post(
        "/api/comments",
        headers=student_headers,
        json={"course_id": course_id, "body": "I should not be able to do this."},
    )
    assert response.status_code == 403
