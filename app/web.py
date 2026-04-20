from datetime import date
from pathlib import Path
from urllib.parse import quote
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.core.database import get_db
from app.models.course import Course
from app.models.mentor_comment import MentorComment
from app.models.note import Note
from app.models.note_folder import NoteFolder
from app.models.quiz_attempt import QuizAttempt
from app.models.study_session import StudySession
from app.models.topic import Topic
from app.models.user import User
from app.schemas.note import NotesPageFilters
from app.schemas.planner import StudyPlanResponse
from app.services.insights import (
    build_course_intelligence,
    build_course_snapshot,
    build_dashboard_insights,
    build_planner_visualization,
)
from app.services.planner import build_study_plan


router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
TOPIC_STATUS_LABELS = {
    "planned": "Запланировано",
    "in_progress": "В процессе",
    "review": "Повторение",
    "done": "Завершено",
}
templates.env.filters["topic_status_label"] = lambda value: TOPIC_STATUS_LABELS.get(value, value)
templates.env.filters["priority_label"] = lambda value: (
    "Критический" if value >= 120 else "Высокий" if value >= 90 else "Средний" if value >= 60 else "Поддерживающий"
)
templates.env.filters["priority_tone"] = lambda value: (
    "risk" if value >= 120 else "attention" if value >= 90 else "good" if value >= 60 else "soft"
)


def render(request: Request, template_name: str, **context: object) -> HTMLResponse:
    context.setdefault("page_message", request.query_params.get("message"))
    return templates.TemplateResponse(request, template_name, context)


def get_owned_course(db: Session, user_id: int, course_id: int) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user_id))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def login_redirect(message: str) -> RedirectResponse:
    return RedirectResponse(url=f"/login?message={quote(message)}", status_code=status.HTTP_303_SEE_OTHER)


def list_filtered_notes(db: Session, user_id: int, filters: NotesPageFilters) -> tuple[list[Note], str]:
    notes_query = select(Note).where(Note.user_id == user_id)
    if filters.folder_id is not None:
        notes_query = notes_query.where(Note.folder_id == filters.folder_id)
    if filters.course_id is not None:
        notes_query = notes_query.where(Note.course_id == filters.course_id)
    search_query = (filters.q or "").strip()
    if search_query:
        pattern = f"%{search_query}%"
        notes_query = notes_query.where(or_(Note.title.ilike(pattern), Note.body.ilike(pattern)))
    notes = db.scalars(notes_query.order_by(Note.is_pinned.desc(), Note.updated_at.desc(), Note.id.desc())).all()
    return notes, search_query


def resolve_selected_note(db: Session, user_id: int, note_id: int | None, notes: list[Note]) -> Note | None:
    if note_id is None:
        return notes[0] if notes else None
    selected_note = db.scalar(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    if selected_note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if any(note.id == selected_note.id for note in notes):
        return selected_note
    return notes[0] if notes else None


def list_note_topics(db: Session, user_id: int, active_course_id: int | None) -> list[Topic]:
    topics_query = (
        select(Topic)
        .join(Course, Topic.course_id == Course.id)
        .where(Course.owner_id == user_id)
        .order_by(Topic.title.asc())
    )
    if active_course_id is not None:
        topics_query = topics_query.where(Topic.course_id == active_course_id)
    return db.scalars(topics_query).all()


def count_notes_by_folder(folders: list[NoteFolder], notes: list[Note]) -> dict[int, int]:
    folder_counts = {folder.id: 0 for folder in folders}
    for note in notes:
        if note.folder_id in folder_counts:
            folder_counts[note.folder_id] += 1
    return folder_counts


@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> HTMLResponse:
    return render(request, "index.html", page_title="StudyForge", current_user=current_user)


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> Response:
    if current_user is not None:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "login.html", page_title="Вход", current_user=current_user)


@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> Response:
    if current_user is not None:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "register.html", page_title="Регистрация", current_user=current_user)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> Response:
    if current_user is None:
        return login_redirect("Войдите, чтобы открыть панель.")
    courses = db.scalars(select(Course).where(Course.owner_id == current_user.id).order_by(Course.exam_date.asc())).all()
    topics = db.scalars(
        select(Topic)
        .join(Course, Topic.course_id == Course.id)
        .where(Course.owner_id == current_user.id)
        .order_by(Topic.id.desc())
    ).all()
    quizzes = db.scalars(
        select(QuizAttempt)
        .join(Topic, QuizAttempt.topic_id == Topic.id)
        .join(Course, Topic.course_id == Course.id)
        .where(Course.owner_id == current_user.id)
    ).all()
    sessions = db.scalars(
        select(StudySession)
        .join(Topic, StudySession.topic_id == Topic.id)
        .join(Course, Topic.course_id == Course.id)
        .where(Course.owner_id == current_user.id)
    ).all()
    dashboard_insights = build_dashboard_insights(
        courses=courses,
        topics=topics,
        attempts=quizzes,
        sessions=sessions,
        today=date.today(),
    )
    avg_mastery = round(sum(topic.mastery_level for topic in topics) / len(topics), 1) if topics else 0
    return render(
        request,
        "dashboard.html",
        page_title="Панель",
        current_user=current_user,
        dashboard_insights=dashboard_insights,
        course_snapshots=dashboard_insights.course_snapshots,
        focus_today=dashboard_insights.focus_today,
        critical_topics=dashboard_insights.critical_topics,
        total_topics=len(topics),
        total_quizzes=len(quizzes),
        avg_mastery=avg_mastery,
    )


@router.get("/courses/{course_id}", response_class=HTMLResponse)
def course_detail_page(
    course_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> Response:
    if current_user is None:
        return login_redirect("Войдите, чтобы открыть курс.")
    course = get_owned_course(db, current_user.id, course_id)
    topics = db.scalars(select(Topic).where(Topic.course_id == course.id).order_by(Topic.id.desc())).all()
    related_notes = db.scalars(
        select(Note)
        .where(Note.user_id == current_user.id, Note.course_id == course.id)
        .order_by(Note.is_pinned.desc(), Note.updated_at.desc(), Note.id.desc())
    ).all()
    study_sessions = db.scalars(
        select(StudySession)
        .join(Topic, StudySession.topic_id == Topic.id)
        .where(Topic.course_id == course.id)
        .order_by(StudySession.id.desc())
    ).all()
    quizzes = db.scalars(
        select(QuizAttempt)
        .join(Topic, QuizAttempt.topic_id == Topic.id)
        .where(Topic.course_id == course.id)
        .order_by(QuizAttempt.id.desc())
    ).all()
    comments = db.scalars(
        select(MentorComment).where(MentorComment.course_id == course.id).order_by(MentorComment.id.desc())
    ).all()
    course_snapshot = build_course_snapshot(
        course=course,
        topics=topics,
        attempts=quizzes,
        sessions=study_sessions,
        today=date.today(),
    )
    course_intelligence = build_course_intelligence(
        course=course,
        topics=topics,
        attempts=quizzes,
        sessions=study_sessions,
        today=date.today(),
    )
    return render(
        request,
        "course_detail.html",
        page_title=course.title,
        current_user=current_user,
        topic_status_labels=TOPIC_STATUS_LABELS,
        course_snapshot=course_snapshot,
        course_intelligence=course_intelligence,
        course=course,
        related_notes=related_notes,
        topics=topics,
        study_sessions=study_sessions,
        quizzes=quizzes,
        comments=comments,
    )


@router.get("/planner/{course_id}", response_class=HTMLResponse)
def planner_page(
    course_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    days: Annotated[int, Query(ge=1, le=14)] = 5,
) -> Response:
    if current_user is None:
        return login_redirect("Войдите, чтобы открыть планировщик.")
    course = get_owned_course(db, current_user.id, course_id)
    topics = db.scalars(select(Topic).where(Topic.course_id == course.id)).all()
    attempts = db.scalars(
        select(QuizAttempt)
        .join(Topic, QuizAttempt.topic_id == Topic.id)
        .where(Topic.course_id == course.id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
    ).all()
    sessions = db.scalars(
        select(StudySession)
        .join(Topic, StudySession.topic_id == Topic.id)
        .where(Topic.course_id == course.id, StudySession.user_id == current_user.id)
        .order_by(StudySession.planned_for.desc())
    ).all()
    course_snapshot = build_course_snapshot(
        course=course,
        topics=topics,
        attempts=attempts,
        sessions=sessions,
        today=date.today(),
    )
    plan: StudyPlanResponse = build_study_plan(course=course, topics=topics, attempts=attempts, days=days)
    planner_visualization = build_planner_visualization(plan=plan, snapshot=course_snapshot)
    return render(
        request,
        "planner.html",
        page_title=f"План: {course.title}",
        current_user=current_user,
        course=course,
        plan=plan,
        planner_visualization=planner_visualization,
        days=days,
        export_url=f"/api/planner/{course.id}/export?days={days}",
    )


@router.get("/notes", response_class=HTMLResponse)
def notes_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    filters: Annotated[NotesPageFilters, Depends()],
) -> Response:
    if current_user is None:
        return login_redirect("Войдите, чтобы открыть заметки.")

    folders = db.scalars(
        select(NoteFolder).where(NoteFolder.user_id == current_user.id).order_by(NoteFolder.name.asc())
    ).all()
    if filters.folder_id is not None and not any(folder.id == filters.folder_id for folder in folders):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    if filters.course_id is not None:
        get_owned_course(db, current_user.id, filters.course_id)

    courses = db.scalars(select(Course).where(Course.owner_id == current_user.id).order_by(Course.title.asc())).all()
    all_notes = db.scalars(
        select(Note).where(Note.user_id == current_user.id).order_by(Note.updated_at.desc(), Note.id.desc())
    ).all()
    notes, search_query = list_filtered_notes(db, current_user.id, filters)
    selected_note = resolve_selected_note(db, current_user.id, filters.note_id, notes)

    active_course_id = filters.course_id
    if active_course_id is None and selected_note is not None:
        active_course_id = selected_note.course_id

    topics = list_note_topics(db, current_user.id, active_course_id)
    folder_counts = count_notes_by_folder(folders, all_notes)
    pinned_notes = [note for note in notes if note.is_pinned]
    regular_notes = [note for note in notes if not note.is_pinned]

    return render(
        request,
        "notes.html",
        page_title="Заметки",
        current_user=current_user,
        folders=folders,
        folder_counts=folder_counts,
        all_notes_count=len(all_notes),
        pinned_notes=pinned_notes,
        regular_notes=regular_notes,
        selected_note=selected_note,
        selected_folder_id=filters.folder_id,
        selected_course_id=active_course_id,
        search_query=search_query,
        courses=courses,
        topics=topics,
    )


@router.get("/logout")
def logout() -> RedirectResponse:
    message = quote("Вы вышли из аккаунта.")
    response = RedirectResponse(
        url=f"/login?message={message}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie("access_token")
    return response
