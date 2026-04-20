from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.quiz_attempt import QuizAttempt
from app.models.topic import Topic
from app.models.user import User
from app.schemas.planner import StudyPlanResponse
from app.services.planner import build_study_plan, render_study_plan_csv


router = APIRouter(prefix="/api/planner", tags=["planner"])


def get_owned_course(db: Session, user_id: int, course_id: int) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user_id))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.get("/{course_id}", response_model=StudyPlanResponse)
def get_study_plan(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: Annotated[int, Query(ge=1, le=14)] = 5,
) -> StudyPlanResponse:
    course = get_owned_course(db, current_user.id, course_id)
    topics = db.scalars(select(Topic).where(Topic.course_id == course.id)).all()
    attempts = db.scalars(
        select(QuizAttempt)
        .join(Topic, QuizAttempt.topic_id == Topic.id)
        .where(Topic.course_id == course.id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
    ).all()
    return build_study_plan(course=course, topics=topics, attempts=attempts, days=days, today=date.today())


@router.get("/{course_id}/export")
def export_study_plan(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: Annotated[int, Query(ge=1, le=14)] = 5,
) -> Response:
    course = get_owned_course(db, current_user.id, course_id)
    topics = db.scalars(select(Topic).where(Topic.course_id == course.id)).all()
    attempts = db.scalars(
        select(QuizAttempt)
        .join(Topic, QuizAttempt.topic_id == Topic.id)
        .where(Topic.course_id == course.id, QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
    ).all()
    plan = build_study_plan(course=course, topics=topics, attempts=attempts, days=days, today=date.today())
    csv_content = "\ufeff" + render_study_plan_csv(plan)
    filename = f"study-plan-{course.id}-{days}-days.csv"
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
