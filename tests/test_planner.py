from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient

from app.models.course import Course
from app.models.topic import Topic
from app.services.planner import build_study_plan


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


def test_build_study_plan_prioritizes_weaker_and_urgent_topic() -> None:
    today = date(2030, 1, 1)
    course = Course(
        id=1,
        owner_id=1,
        title="Probability",
        description="Probability course",
        exam_date=date(2030, 1, 10),
        target_score=95,
        weekly_hours_goal=7,
        color_theme="mint",
    )
    weak_topic = Topic(
        id=1,
        course_id=1,
        title="Bayes Rule",
        description="Conditional probability",
        difficulty=5,
        importance=5,
        estimated_minutes=120,
        mastery_level=20,
        last_reviewed_at=datetime(2029, 12, 10, 10, 0, 0),
        status="planned",
    )
    strong_topic = Topic(
        id=2,
        course_id=1,
        title="Combinatorics",
        description="Counting methods",
        difficulty=3,
        importance=3,
        estimated_minutes=90,
        mastery_level=80,
        last_reviewed_at=datetime(2029, 12, 31, 10, 0, 0),
        status="planned",
    )

    plan = build_study_plan(course=course, topics=[weak_topic, strong_topic], days=3, today=today)

    assert len(plan.recommendations) == 3
    assert plan.recommendations[0].topic_id == 1
    assert plan.recommendations[0].priority_score > plan.recommendations[1].priority_score


def test_planner_endpoint_returns_multiday_plan(client: TestClient) -> None:
    headers = auth_headers(client, "ada@example.com")
    course_response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Algorithms",
            "description": "Algorithms course",
            "exam_date": (date.today() + timedelta(days=14)).isoformat(),
            "target_score": 93,
            "weekly_hours_goal": 10,
            "color_theme": "ocean",
        },
    )
    course_id = course_response.json()["id"]

    client.post(
        "/api/topics",
        headers=headers,
        json={
            "course_id": course_id,
            "title": "Dynamic Programming",
            "description": "DP patterns",
            "difficulty": 5,
            "importance": 5,
            "estimated_minutes": 150,
            "mastery_level": 25,
            "status": "planned",
        },
    )
    client.post(
        "/api/topics",
        headers=headers,
        json={
            "course_id": course_id,
            "title": "Graphs",
            "description": "Graph algorithms",
            "difficulty": 4,
            "importance": 4,
            "estimated_minutes": 120,
            "mastery_level": 50,
            "status": "planned",
        },
    )

    response = client.get(f"/api/planner/{course_id}?days=2", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["course_id"] == course_id
    assert len(body["recommendations"]) == 2
    assert body["recommendations"][0]["recommended_minutes"] > 0


def test_planner_export_returns_csv(client: TestClient) -> None:
    headers = auth_headers(client, "grace@example.com")
    course_response = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Systems Biology",
            "description": "Systems biology course",
            "exam_date": (date.today() + timedelta(days=10)).isoformat(),
            "target_score": 90,
            "weekly_hours_goal": 9,
            "color_theme": "forest",
        },
    )
    course_id = course_response.json()["id"]

    client.post(
        "/api/topics",
        headers=headers,
        json={
            "course_id": course_id,
            "title": "Gene Regulation",
            "description": "Regulatory circuits",
            "difficulty": 4,
            "importance": 5,
            "estimated_minutes": 140,
            "mastery_level": 35,
            "status": "planned",
        },
    )

    response = client.get(f"/api/planner/{course_id}/export?days=3", headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "planned_for,topic_title,recommended_minutes,priority_score,reason" in response.text
    assert "Gene Regulation" in response.text
