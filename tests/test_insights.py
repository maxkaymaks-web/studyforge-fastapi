from datetime import date, datetime, timedelta

from app.models.course import Course
from app.models.quiz_attempt import QuizAttempt
from app.models.study_session import StudySession
from app.models.topic import Topic
from app.services import insights
from app.services.planner import build_study_plan


def build_course(course_id: int, title: str, exam_date: date) -> Course:
    return Course(
        id=course_id,
        owner_id=1,
        title=title,
        description=f"{title} course",
        exam_date=exam_date,
        target_score=92,
        weekly_hours_goal=8,
        color_theme="ocean",
    )


def build_topic(
    topic_id: int,
    course_id: int,
    title: str,
    mastery_level: int,
    status: str,
    *,
    importance: int = 5,
    difficulty: int = 4,
    estimated_minutes: int = 120,
    last_reviewed_at: datetime | None = None,
) -> Topic:
    return Topic(
        id=topic_id,
        course_id=course_id,
        title=title,
        description=f"{title} topic",
        difficulty=difficulty,
        importance=importance,
        estimated_minutes=estimated_minutes,
        mastery_level=mastery_level,
        status=status,
        last_reviewed_at=last_reviewed_at,
    )


def build_session(session_id: int, topic_id: int, planned_for: date, actual_minutes: int) -> StudySession:
    return StudySession(
        id=session_id,
        topic_id=topic_id,
        user_id=1,
        planned_for=planned_for,
        actual_minutes=actual_minutes,
        focus_score=8,
        notes="Focused study block",
    )


def build_attempt(attempt_id: int, topic_id: int, attempted_at: datetime, score: int, max_score: int) -> QuizAttempt:
    return QuizAttempt(
        id=attempt_id,
        topic_id=topic_id,
        user_id=1,
        score=score,
        max_score=max_score,
        attempted_at=attempted_at,
    )


def test_dashboard_insights_expose_new_analytics_layers() -> None:
    today = date(2030, 1, 10)
    urgent_course = build_course(1, "Probability", today + timedelta(days=5))
    steady_course = build_course(2, "Linear Algebra", today + timedelta(days=18))

    topics = [
        build_topic(
            1,
            1,
            "Bayes",
            32,
            "planned",
            last_reviewed_at=datetime(2030, 1, 2, 9, 0, 0),
        ),
        build_topic(
            2,
            1,
            "Markov Chains",
            44,
            "in_progress",
            last_reviewed_at=datetime(2030, 1, 7, 10, 0, 0),
        ),
        build_topic(
            3,
            2,
            "Eigenvectors",
            76,
            "review",
            importance=4,
            difficulty=3,
            last_reviewed_at=datetime(2030, 1, 9, 11, 0, 0),
        ),
    ]
    sessions = [
        build_session(1, 1, today - timedelta(days=2), 70),
        build_session(2, 2, today - timedelta(days=1), 80),
        build_session(3, 1, today, 60),
        build_session(4, 3, today - timedelta(days=4), 45),
    ]
    attempts = [
        build_attempt(1, 1, datetime(2030, 1, 3, 12, 0, 0), 28, 50),
        build_attempt(2, 2, datetime(2030, 1, 8, 12, 0, 0), 34, 50),
        build_attempt(3, 1, datetime(2030, 1, 10, 12, 0, 0), 40, 50),
    ]

    dashboard = insights.build_dashboard_insights(
        courses=[urgent_course, steady_course],
        topics=topics,
        attempts=attempts,
        sessions=sessions,
        today=today,
    )

    assert dashboard.streak_days == 3
    assert dashboard.health_score > 0
    assert len(dashboard.weekly_load) == 7
    assert dashboard.weekly_load[-1].minutes == 60
    assert len(dashboard.quiz_trend) == 3
    assert dashboard.upcoming_deadlines[0].course_title == "Probability"
    assert dashboard.course_risks[0].course_title == "Probability"
    assert any(item.title for item in dashboard.achievements)


def test_course_intelligence_surfaces_distribution_blockers_and_next_action() -> None:
    today = date(2030, 1, 10)
    course = build_course(1, "Probability", today + timedelta(days=5))
    topics = [
        build_topic(1, 1, "Bayes", 30, "planned", last_reviewed_at=datetime(2030, 1, 1, 9, 0, 0)),
        build_topic(2, 1, "Markov Chains", 48, "in_progress", last_reviewed_at=datetime(2030, 1, 7, 9, 0, 0)),
        build_topic(3, 1, "Random Variables", 82, "done", last_reviewed_at=datetime(2030, 1, 9, 9, 0, 0)),
    ]
    sessions = [
        build_session(1, 1, today - timedelta(days=1), 90),
        build_session(2, 2, today, 60),
    ]
    attempts = [
        build_attempt(1, 1, datetime(2030, 1, 4, 12, 0, 0), 22, 50),
        build_attempt(2, 2, datetime(2030, 1, 9, 12, 0, 0), 35, 50),
    ]

    intelligence = insights.build_course_intelligence(
        course=course,
        topics=topics,
        attempts=attempts,
        sessions=sessions,
        today=today,
    )

    assert sum(item.count for item in intelligence.status_distribution) == 3
    assert intelligence.recent_quiz_trend[-1].value == 70
    assert intelligence.blockers
    assert intelligence.next_action_title
    assert intelligence.next_action_href == "/planner/1"


def test_planner_visualization_projects_readiness_gain() -> None:
    today = date(2030, 1, 10)
    course = build_course(1, "Probability", today + timedelta(days=5))
    topics = [
        build_topic(1, 1, "Bayes", 35, "planned", estimated_minutes=100, last_reviewed_at=datetime(2030, 1, 2, 9, 0, 0)),
        build_topic(2, 1, "Markov Chains", 42, "in_progress", estimated_minutes=110, last_reviewed_at=datetime(2030, 1, 6, 9, 0, 0)),
    ]
    attempts = [
        build_attempt(1, 1, datetime(2030, 1, 4, 12, 0, 0), 24, 50),
    ]
    sessions = [
        build_session(1, 1, today - timedelta(days=1), 75),
        build_session(2, 2, today, 60),
    ]

    snapshot = insights.build_course_snapshot(course=course, topics=topics, attempts=attempts, sessions=sessions, today=today)
    plan = build_study_plan(course=course, topics=topics, attempts=attempts, days=4, today=today)

    visualization = insights.build_planner_visualization(plan=plan, snapshot=snapshot)

    assert len(visualization.daily_load) == 4
    assert visualization.projected_readiness_percent >= snapshot.readiness_percent
    assert visualization.projected_delta >= 0
    assert visualization.projected_readiness_label
