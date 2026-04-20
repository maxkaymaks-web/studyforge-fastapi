from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.study_session import StudySession
from app.models.topic import Topic
from app.models.user import User
from app.schemas.study_session import StudySessionCreate, StudySessionRead, StudySessionUpdate


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def get_owned_topic(db: Session, user_id: int, topic_id: int) -> Topic:
    topic = db.scalar(
        select(Topic)
        .join(Course, Topic.course_id == Course.id)
        .where(Topic.id == topic_id, Course.owner_id == user_id)
    )
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic


def get_owned_session(db: Session, user_id: int, session_id: int) -> StudySession:
    study_session = db.scalar(
        select(StudySession)
        .join(Topic, StudySession.topic_id == Topic.id)
        .join(Course, Topic.course_id == Course.id)
        .where(StudySession.id == session_id, Course.owner_id == user_id)
    )
    if study_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study session not found")
    return study_session


@router.post("", response_model=StudySessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: StudySessionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudySessionRead:
    topic = get_owned_topic(db, current_user.id, payload.topic_id)
    study_session = StudySession(user_id=current_user.id, **payload.model_dump())
    topic.last_reviewed_at = datetime.utcnow()
    db.add(study_session)
    db.add(topic)
    db.commit()
    db.refresh(study_session)
    return StudySessionRead.model_validate(study_session)


@router.get("", response_model=list[StudySessionRead])
def list_sessions(
    topic_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[StudySessionRead]:
    get_owned_topic(db, current_user.id, topic_id)
    sessions = db.scalars(
        select(StudySession).where(StudySession.topic_id == topic_id).order_by(StudySession.id.desc())
    ).all()
    return [StudySessionRead.model_validate(session_item) for session_item in sessions]


@router.get("/{session_id}", response_model=StudySessionRead)
def get_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudySessionRead:
    study_session = get_owned_session(db, current_user.id, session_id)
    return StudySessionRead.model_validate(study_session)


@router.put("/{session_id}", response_model=StudySessionRead)
def update_session(
    session_id: int,
    payload: StudySessionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StudySessionRead:
    study_session = get_owned_session(db, current_user.id, session_id)
    for field, value in payload.model_dump().items():
        setattr(study_session, field, value)
    topic = get_owned_topic(db, current_user.id, study_session.topic_id)
    topic.last_reviewed_at = datetime.utcnow()
    db.add(study_session)
    db.add(topic)
    db.commit()
    db.refresh(study_session)
    return StudySessionRead.model_validate(study_session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    study_session = get_owned_session(db, current_user.id, session_id)
    db.delete(study_session)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

