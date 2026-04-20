from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.quiz_attempt import QuizAttempt
from app.models.topic import Topic
from app.models.user import User
from app.schemas.quiz_attempt import QuizAttemptCreate, QuizAttemptRead, QuizAttemptUpdate


router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


def get_owned_topic(db: Session, user_id: int, topic_id: int) -> Topic:
    topic = db.scalar(
        select(Topic)
        .join(Course, Topic.course_id == Course.id)
        .where(Topic.id == topic_id, Course.owner_id == user_id)
    )
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic


def get_owned_quiz_attempt(db: Session, user_id: int, attempt_id: int) -> QuizAttempt:
    attempt = db.scalar(
        select(QuizAttempt)
        .join(Topic, QuizAttempt.topic_id == Topic.id)
        .join(Course, Topic.course_id == Course.id)
        .where(QuizAttempt.id == attempt_id, Course.owner_id == user_id)
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz attempt not found")
    return attempt


def recompute_mastery(topic: Topic, score: int, max_score: int) -> None:
    topic.mastery_level = max(0, min(100, round(score / max_score * 100)))


@router.post("", response_model=QuizAttemptRead, status_code=status.HTTP_201_CREATED)
def create_quiz_attempt(
    payload: QuizAttemptCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QuizAttemptRead:
    topic = get_owned_topic(db, current_user.id, payload.topic_id)
    attempt = QuizAttempt(topic_id=topic.id, user_id=current_user.id, **payload.model_dump(exclude={"topic_id"}))
    recompute_mastery(topic, payload.score, payload.max_score)
    db.add(attempt)
    db.add(topic)
    db.commit()
    db.refresh(attempt)
    return QuizAttemptRead.model_validate(attempt)


@router.get("", response_model=list[QuizAttemptRead])
def list_quiz_attempts(
    topic_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[QuizAttemptRead]:
    get_owned_topic(db, current_user.id, topic_id)
    attempts = db.scalars(
        select(QuizAttempt).where(QuizAttempt.topic_id == topic_id).order_by(QuizAttempt.id.desc())
    ).all()
    return [QuizAttemptRead.model_validate(attempt) for attempt in attempts]


@router.get("/{attempt_id}", response_model=QuizAttemptRead)
def get_quiz_attempt(
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QuizAttemptRead:
    attempt = get_owned_quiz_attempt(db, current_user.id, attempt_id)
    return QuizAttemptRead.model_validate(attempt)


@router.put("/{attempt_id}", response_model=QuizAttemptRead)
def update_quiz_attempt(
    attempt_id: int,
    payload: QuizAttemptUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QuizAttemptRead:
    attempt = get_owned_quiz_attempt(db, current_user.id, attempt_id)
    for field, value in payload.model_dump().items():
        setattr(attempt, field, value)
    topic = get_owned_topic(db, current_user.id, attempt.topic_id)
    recompute_mastery(topic, payload.score, payload.max_score)
    db.add(attempt)
    db.add(topic)
    db.commit()
    db.refresh(attempt)
    return QuizAttemptRead.model_validate(attempt)


@router.delete("/{attempt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz_attempt(
    attempt_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    attempt = get_owned_quiz_attempt(db, current_user.id, attempt_id)
    db.delete(attempt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

