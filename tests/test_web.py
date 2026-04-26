from fastapi.testclient import TestClient


def register_and_login(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "supersecure123",
            "role": "student",
        },
    )
    client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "supersecure123"},
    )


def create_course(client: TestClient) -> int:
    response = client.post(
        "/api/courses",
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


def create_topic(client: TestClient, course_id: int) -> int:
    response = client.post(
        "/api/topics",
        json={
            "course_id": course_id,
            "title": "Динамическое программирование",
            "description": "Базовые шаблоны состояний",
            "difficulty": 5,
            "importance": 5,
            "estimated_minutes": 150,
            "mastery_level": 20,
            "status": "planned",
        },
    )
    return response.json()["id"]


def create_session(client: TestClient, topic_id: int) -> int:
    response = client.post(
        "/api/sessions",
        json={
            "topic_id": topic_id,
            "planned_for": "2026-04-21",
            "actual_minutes": 90,
            "focus_score": 8,
            "notes": "Разобрал основные паттерны",
        },
    )
    return response.json()["id"]


def create_quiz(client: TestClient, topic_id: int) -> int:
    response = client.post(
        "/api/quizzes",
        json={
            "topic_id": topic_id,
            "score": 42,
            "max_score": 50,
        },
    )
    return response.json()["id"]


def create_folder(client: TestClient) -> int:
    response = client.post(
        "/api/note-folders",
        json={
            "name": "Учебные заметки",
        },
    )
    return response.json()["id"]


def create_note(
    client: TestClient,
    folder_id: int | None = None,
    course_id: int | None = None,
    topic_id: int | None = None,
    title: str = "Конспект по теме",
    body: str = "Короткое превью заметки для интерфейса.",
    is_pinned: bool = True,
) -> int:
    response = client.post(
        "/api/notes",
        json={
            "title": title,
            "body": body,
            "folder_id": folder_id,
            "course_id": course_id,
            "topic_id": topic_id,
            "color_tone": "sunny",
            "is_pinned": is_pinned,
        },
    )
    return response.json()["id"]


def test_public_pages_render(client: TestClient) -> None:
    home_response = client.get("/")
    login_response = client.get("/login")
    register_response = client.get("/register")

    assert home_response.status_code == 200
    assert login_response.status_code == 200
    assert register_response.status_code == 200
    assert "StudyForge" in home_response.text


def test_home_page_uses_product_copy(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Умный план на каждый день" in response.text
    assert "Прогресс без ручных таблиц" in response.text
    assert "Подготовка как реальный процесс" in response.text
    assert "Ядро приоритизации" not in response.text
    assert "Подходит для защиты" not in response.text
    assert "Все ключевые требования" not in response.text
    assert "CRUD, JWT, алгоритм планирования, тесты и отчёт pylint" not in response.text


def test_home_page_hides_guest_actions_for_logged_in_user(client: TestClient) -> None:
    register_and_login(client)

    response = client.get("/")

    assert response.status_code == 200
    assert 'href="/logout"' in response.text
    assert 'href="/notes"' in response.text
    assert "Войти в аккаунт" not in response.text
    assert 'href="/login"' not in response.text
    assert 'href="/register"' not in response.text


def test_auth_pages_redirect_for_logged_in_user(client: TestClient) -> None:
    register_and_login(client)

    login_response = client.get("/login", follow_redirects=False)
    register_response = client.get("/register", follow_redirects=False)

    assert login_response.status_code in {302, 303, 307}
    assert login_response.headers["location"] == "/dashboard"
    assert register_response.status_code in {302, 303, 307}
    assert register_response.headers["location"] == "/dashboard"


def test_dashboard_and_course_pages_render_for_logged_in_user(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)

    dashboard_response = client.get("/dashboard")
    course_response = client.get(f"/courses/{course_id}")
    planner_response = client.get(f"/planner/{course_id}")
    notes_response = client.get("/notes")

    assert dashboard_response.status_code == 200
    assert course_response.status_code == 200
    assert planner_response.status_code == 200
    assert notes_response.status_code == 200
    assert "Algorithms" in course_response.text


def test_dashboard_shows_focus_and_risk_sections(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    topic_id = create_topic(client, course_id)
    create_session(client, topic_id)
    create_quiz(client, topic_id)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Фокус на сегодня" in response.text
    assert "Критические темы" in response.text
    assert "Готовность" in response.text
    assert "Серия учебных дней" in response.text
    assert "Подготовка по неделе" in response.text
    assert "Ближайшие дедлайны" in response.text
    assert "Достижения" in response.text
    assert "Динамическое программирование" in response.text


def test_dashboard_uses_russian_ui_copy(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    topic_id = create_topic(client, course_id)
    create_session(client, topic_id)
    create_quiz(client, topic_id)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Индекс устойчивости" in response.text
    assert "Достижения" in response.text
    assert "Health score" not in response.text
    assert "milestones" not in response.text


def test_protected_pages_redirect_to_login(client: TestClient) -> None:
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in {302, 303, 307}
    assert response.headers["location"].startswith("/login")


def test_course_page_localizes_topic_status(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    create_topic(client, course_id)

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert "Запланировано" in response.text
    assert "planned ·" not in response.text


def test_course_page_shows_management_actions(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    create_topic(client, course_id)

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert "Удалить курс" in response.text
    assert "Сохранить изменения" in response.text
    assert "Удалить тему" in response.text
    assert "Удалить сессию" in response.text or "Сессий пока нет" in response.text
    assert "Удалить результат" in response.text or "Самопроверок пока нет" in response.text


def test_course_page_shows_professional_insights(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    topic_id = create_topic(client, course_id)
    create_session(client, topic_id)
    create_quiz(client, topic_id)
    folder_id = create_folder(client)
    create_note(client, folder_id=folder_id, course_id=course_id, topic_id=topic_id)

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert "Готовность курса" in response.text
    assert "Средний результат тестов" in response.text
    assert "Минут занятий" in response.text
    assert "Следующая тема" in response.text
    assert "Распределение тем" in response.text
    assert "Что мешает выйти на цель" in response.text
    assert "Быстрые действия" in response.text
    assert "Связанные заметки" in response.text
    assert "Конспект по теме" in response.text


def test_course_page_hides_topic_dependent_forms_without_topics(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert "Сначала добавьте хотя бы одну тему." in response.text
    assert "Сохранить сессию" not in response.text
    assert "Сохранить результат" not in response.text


def test_logout_clears_session(client: TestClient) -> None:
    register_and_login(client)

    logout_response = client.get("/logout", follow_redirects=False)
    assert logout_response.status_code in {302, 303, 307}
    assert logout_response.headers["location"].startswith("/login")

    dashboard_response = client.get("/dashboard", follow_redirects=False)
    assert dashboard_response.status_code in {302, 303, 307}


def test_favicon_is_available(client: TestClient) -> None:
    response = client.get("/static/favicon.svg")
    assert response.status_code == 200


def test_planner_page_shows_professional_summary_and_export(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    topic_id = create_topic(client, course_id)
    create_quiz(client, topic_id)

    response = client.get(f"/planner/{course_id}?days=7")

    assert response.status_code == 200
    assert "Средняя нагрузка в день" in response.text
    assert "Дней до экзамена" in response.text
    assert "Индекс приоритета" in response.text
    assert "Экспорт CSV" in response.text
    assert "Нагрузка по дням" in response.text
    assert "Прогноз готовности" in response.text
    assert "Легенда приоритетов" in response.text


def test_notes_page_renders_workspace_like_notes_app(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    topic_id = create_topic(client, course_id)
    folder_id = create_folder(client)
    create_note(client, folder_id=folder_id, course_id=course_id, topic_id=topic_id)

    response = client.get("/notes")

    assert response.status_code == 200
    assert "Папки" in response.text
    assert "Все заметки" in response.text
    assert "Закреплённые" in response.text
    assert "Редактор заметки" in response.text
    assert "Конспект по теме" in response.text


def test_notes_page_uses_russian_ui_copy(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    topic_id = create_topic(client, course_id)
    folder_id = create_folder(client)
    create_note(client, folder_id=folder_id, course_id=course_id, topic_id=topic_id)

    response = client.get("/notes")

    assert response.status_code == 200
    assert "База знаний" in response.text
    assert "Закреплено" in response.text
    assert "Редактор" in response.text
    assert "Knowledge layer" not in response.text
    assert "Pinned" not in response.text
    assert "Editor" not in response.text
    assert "workspace" not in response.text


def test_notes_page_limits_topic_options_to_selected_course(client: TestClient) -> None:
    register_and_login(client)
    first_course_id = create_course(client)
    first_topic_id = create_topic(client, first_course_id)
    second_course_response = client.post(
        "/api/courses",
        json={
            "title": "Databases",
            "description": "Databases course",
            "exam_date": "2026-07-10",
            "target_score": 88,
            "weekly_hours_goal": 8,
            "color_theme": "forest",
        },
    )
    second_course_id = second_course_response.json()["id"]
    client.post(
        "/api/topics",
        json={
            "course_id": second_course_id,
            "title": "Normalization",
            "description": "Database normalization",
            "difficulty": 4,
            "importance": 4,
            "estimated_minutes": 120,
            "mastery_level": 40,
            "status": "planned",
        },
    )
    folder_id = create_folder(client)
    note_id = create_note(client, folder_id=folder_id, course_id=first_course_id, topic_id=first_topic_id)

    response = client.get(f"/notes?course_id={first_course_id}&note_id={note_id}")

    assert response.status_code == 200
    assert "Динамическое программирование" in response.text
    assert "Normalization · Databases" not in response.text


def test_notes_page_does_not_open_note_from_another_course_filter(client: TestClient) -> None:
    register_and_login(client)
    first_course_id = create_course(client)
    first_topic_id = create_topic(client, first_course_id)
    second_course_response = client.post(
        "/api/courses",
        json={
            "title": "Databases",
            "description": "Databases course",
            "exam_date": "2026-07-10",
            "target_score": 88,
            "weekly_hours_goal": 8,
            "color_theme": "forest",
        },
    )
    second_course_id = second_course_response.json()["id"]
    second_topic_response = client.post(
        "/api/topics",
        json={
            "course_id": second_course_id,
            "title": "Normalization",
            "description": "Database normalization",
            "difficulty": 4,
            "importance": 4,
            "estimated_minutes": 120,
            "mastery_level": 40,
            "status": "planned",
        },
    )
    second_topic_id = second_topic_response.json()["id"]
    folder_id = create_folder(client)
    create_note(
        client,
        folder_id=folder_id,
        course_id=first_course_id,
        topic_id=first_topic_id,
        title="Заметка по алгоритмам",
        is_pinned=True,
    )
    other_note_id = create_note(
        client,
        folder_id=folder_id,
        course_id=second_course_id,
        topic_id=second_topic_id,
        title="Заметка по базам",
        is_pinned=False,
    )

    response = client.get(f"/notes?course_id={first_course_id}&note_id={other_note_id}")

    assert response.status_code == 200
    assert 'value="Заметка по алгоритмам"' in response.text
    assert 'value="Заметка по базам"' not in response.text


def test_course_page_uses_russian_notes_labels(client: TestClient) -> None:
    register_and_login(client)
    course_id = create_course(client)
    topic_id = create_topic(client, course_id)
    folder_id = create_folder(client)
    create_note(client, folder_id=folder_id, course_id=course_id, topic_id=topic_id)

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert "База знаний" in response.text
    assert "Закреплено" in response.text
    assert "Knowledge layer" not in response.text
    assert "Pinned" not in response.text
    assert "Notes workspace" not in response.text
