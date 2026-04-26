from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.mentor_comment import MentorComment
from app.models.note import Note
from app.models.note_folder import NoteFolder
from app.models.quiz_attempt import QuizAttempt
from app.models.study_session import StudySession
from app.models.topic import Topic
from app.models.user import User
from app.services.demo_seed import DEMO_EMAIL, DEMO_MENTOR_EMAIL, seed_demo_account


def test_seed_demo_account_creates_full_demo_workspace(db_session: Session) -> None:
    result = seed_demo_account(db_session, password="demo-pass-123", today=date(2026, 4, 20))

    demo_user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    mentor_user = db_session.scalar(select(User).where(User.email == DEMO_MENTOR_EMAIL))
    courses = db_session.scalars(select(Course).where(Course.owner_id == demo_user.id).order_by(Course.id)).all()
    topics = db_session.scalars(
        select(Topic).join(Course, Topic.course_id == Course.id).where(Course.owner_id == demo_user.id)
    ).all()
    sessions = db_session.scalars(select(StudySession).where(StudySession.user_id == demo_user.id)).all()
    quizzes = db_session.scalars(select(QuizAttempt).where(QuizAttempt.user_id == demo_user.id)).all()
    comments = db_session.scalars(
        select(MentorComment).join(Course, MentorComment.course_id == Course.id).where(Course.owner_id == demo_user.id)
    ).all()
    folders = db_session.scalars(select(NoteFolder).where(NoteFolder.user_id == demo_user.id)).all()
    notes = db_session.scalars(select(Note).where(Note.user_id == demo_user.id)).all()

    assert result.email == DEMO_EMAIL
    assert demo_user is not None
    assert mentor_user is not None
    assert len(courses) == 2
    assert len(topics) >= 6
    assert len(sessions) >= 6
    assert len(quizzes) >= 5
    assert len(comments) >= 3
    assert len(folders) >= 3
    assert len(notes) >= 4


def test_seed_demo_account_is_idempotent(db_session: Session) -> None:
    first = seed_demo_account(db_session, password="demo-pass-123", today=date(2026, 4, 20))
    second = seed_demo_account(db_session, password="demo-pass-123", today=date(2026, 4, 20))

    demo_user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    courses = db_session.scalars(select(Course).where(Course.owner_id == demo_user.id)).all()
    topics = db_session.scalars(
        select(Topic).join(Course, Topic.course_id == Course.id).where(Course.owner_id == demo_user.id)
    ).all()
    sessions = db_session.scalars(select(StudySession).where(StudySession.user_id == demo_user.id)).all()
    quizzes = db_session.scalars(select(QuizAttempt).where(QuizAttempt.user_id == demo_user.id)).all()
    comments = db_session.scalars(
        select(MentorComment).join(Course, MentorComment.course_id == Course.id).where(Course.owner_id == demo_user.id)
    ).all()
    folders = db_session.scalars(select(NoteFolder).where(NoteFolder.user_id == demo_user.id)).all()
    notes = db_session.scalars(select(Note).where(Note.user_id == demo_user.id)).all()

    assert first.email == second.email
    assert len(courses) == 2
    assert len(topics) >= 6
    assert len(sessions) >= 6
    assert len(quizzes) >= 5
    assert len(comments) >= 3
    assert len(folders) >= 3
    assert len(notes) >= 4


def test_seed_demo_account_uses_localized_video_pitch_copy(db_session: Session) -> None:
    seed_demo_account(db_session, password="demo-pass-123", today=date(2026, 4, 20))

    demo_user = db_session.scalar(select(User).where(User.email == DEMO_EMAIL))
    pitch_note = db_session.scalar(
        select(Note).where(Note.user_id == demo_user.id, Note.title == "Идея для видео-защиты")
    )

    assert pitch_note is not None
    assert "Показать сначала панель" in pitch_note.body
    assert "cockpit dashboard" not in pitch_note.body
    assert "course intelligence" not in pitch_note.body
    assert "notes workspace" not in pitch_note.body
