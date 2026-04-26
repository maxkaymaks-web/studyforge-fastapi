from fastapi.testclient import TestClient


def auth_headers(client: TestClient, email: str = "notes@example.com") -> dict[str, str]:
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Notes User",
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
            "description": "Algorithms course",
            "exam_date": "2026-06-15",
            "target_score": 93,
            "weekly_hours_goal": 10,
            "color_theme": "ocean",
        },
    )
    return response.json()["id"]


def create_topic(client: TestClient, headers: dict[str, str], course_id: int) -> int:
    response = client.post(
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
    return response.json()["id"]


def test_notes_and_folders_crud_with_filters(client: TestClient) -> None:
    headers = auth_headers(client)
    course_id = create_course(client, headers)
    topic_id = create_topic(client, headers, course_id)

    folder_one_response = client.post("/api/note-folders", headers=headers, json={"name": "Учёба"})
    folder_two_response = client.post("/api/note-folders", headers=headers, json={"name": "Идеи"})
    folder_one_id = folder_one_response.json()["id"]
    folder_two_id = folder_two_response.json()["id"]

    note_one_response = client.post(
        "/api/notes",
        headers=headers,
        json={
            "title": "Разбор динамики",
            "body": "- [ ] повторить рюкзак\n- [x] выписать переходы",
            "folder_id": folder_one_id,
            "course_id": course_id,
            "topic_id": topic_id,
            "color_tone": "sunny",
            "is_pinned": True,
        },
    )
    note_two_response = client.post(
        "/api/notes",
        headers=headers,
        json={
            "title": "Идея проекта",
            "body": "Сделать мини-симулятор маршрутов.",
            "folder_id": folder_two_id,
            "color_tone": "mint",
            "is_pinned": False,
        },
    )
    note_one_id = note_one_response.json()["id"]
    note_two_id = note_two_response.json()["id"]

    list_response = client.get("/api/notes", headers=headers)
    folder_response = client.get(f"/api/notes?folder_id={folder_one_id}", headers=headers)
    course_response = client.get(f"/api/notes?course_id={course_id}", headers=headers)
    topic_response = client.get(f"/api/notes?topic_id={topic_id}", headers=headers)
    pinned_response = client.get("/api/notes?pinned=true", headers=headers)
    search_response = client.get("/api/notes?q=динамики", headers=headers)

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == note_one_id
    assert folder_response.json()[0]["id"] == note_one_id
    assert course_response.json()[0]["id"] == note_one_id
    assert topic_response.json()[0]["id"] == note_one_id
    assert pinned_response.json()[0]["id"] == note_one_id
    assert search_response.json()[0]["id"] == note_one_id

    update_response = client.put(
        f"/api/notes/{note_two_id}",
        headers=headers,
        json={
            "title": "Идея продукта",
            "body": "Нужен режим заметок как в Apple Notes.",
            "folder_id": folder_one_id,
            "course_id": None,
            "topic_id": None,
            "color_tone": "rose",
            "is_pinned": True,
        },
    )
    get_response = client.get(f"/api/notes/{note_two_id}", headers=headers)
    rename_folder_response = client.put(
        f"/api/note-folders/{folder_two_id}",
        headers=headers,
        json={"name": "Вдохновение"},
    )

    assert update_response.status_code == 200
    assert get_response.json()["title"] == "Идея продукта"
    assert get_response.json()["is_pinned"] is True
    assert rename_folder_response.json()["name"] == "Вдохновение"

    delete_note_response = client.delete(f"/api/notes/{note_two_id}", headers=headers)

    assert delete_note_response.status_code == 204


def test_note_references_are_cleared_when_folder_course_or_topic_are_deleted(client: TestClient) -> None:
    headers = auth_headers(client, "cleanup@example.com")
    course_id = create_course(client, headers)
    topic_id = create_topic(client, headers, course_id)
    folder_response = client.post("/api/note-folders", headers=headers, json={"name": "Быстрые заметки"})
    folder_id = folder_response.json()["id"]
    note_response = client.post(
        "/api/notes",
        headers=headers,
        json={
            "title": "Привязанная заметка",
            "body": "Проверить удаление привязок.",
            "folder_id": folder_id,
            "course_id": course_id,
            "topic_id": topic_id,
            "color_tone": "lavender",
            "is_pinned": False,
        },
    )
    note_id = note_response.json()["id"]

    folder_delete_response = client.delete(f"/api/note-folders/{folder_id}", headers=headers)
    after_folder = client.get(f"/api/notes/{note_id}", headers=headers)

    assert folder_delete_response.status_code == 204
    assert after_folder.json()["folder_id"] is None

    topic_delete_response = client.delete(f"/api/topics/{topic_id}", headers=headers)
    after_topic = client.get(f"/api/notes/{note_id}", headers=headers)

    assert topic_delete_response.status_code == 204
    assert after_topic.json()["topic_id"] is None

    course_delete_response = client.delete(f"/api/courses/{course_id}", headers=headers)
    after_course = client.get(f"/api/notes/{note_id}", headers=headers)

    assert course_delete_response.status_code == 204
    assert after_course.json()["course_id"] is None


def test_note_rejects_topic_that_does_not_match_course(client: TestClient) -> None:
    headers = auth_headers(client, "validation@example.com")
    course_id = create_course(client, headers)
    second_course_id = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Databases",
            "description": "Databases course",
            "exam_date": "2026-07-10",
            "target_score": 88,
            "weekly_hours_goal": 8,
            "color_theme": "forest",
        },
    ).json()["id"]
    topic_id = create_topic(client, headers, course_id)

    response = client.post(
        "/api/notes",
        headers=headers,
        json={
            "title": "Несовпадающая привязка",
            "body": "Такую заметку создавать нельзя.",
            "course_id": second_course_id,
            "topic_id": topic_id,
            "color_tone": "sunny",
            "is_pinned": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Topic does not belong to the selected course"
