from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.course import Course
from app.models.topic import Topic
from app.models.user import User


def test_tables_can_be_created() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    table_names = set(Base.metadata.tables.keys())
    assert "users" in table_names
    assert "courses" in table_names
    assert "topics" in table_names


def test_user_course_topic_relationships_persist() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            full_name="Test Student",
            email="student@example.com",
            password_hash="hash",
            role="student",
        )
        session.add(user)
        session.flush()

        course = Course(
            owner_id=user.id,
            title="Linear Algebra",
            description="Matrices and vectors",
            exam_date=date(2026, 6, 1),
            target_score=95,
            weekly_hours_goal=8,
            color_theme="emerald",
        )
        session.add(course)
        session.flush()

        topic = Topic(
            course_id=course.id,
            title="Determinants",
            description="Core rules",
            difficulty=4,
            importance=5,
            estimated_minutes=120,
            mastery_level=20,
            status="planned",
        )
        session.add(topic)
        session.commit()

    with Session(engine) as session:
        saved_user = session.scalar(select(User).where(User.email == "student@example.com"))
        assert saved_user is not None
        assert len(saved_user.courses) == 1
        assert saved_user.courses[0].topics[0].title == "Determinants"
