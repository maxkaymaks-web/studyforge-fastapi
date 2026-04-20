from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.note import Note
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicRead, TopicUpdate


router = APIRouter(prefix="/api/topics", tags=["topics"])


def get_owned_course(db: Session, user_id: int, course_id: int) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user_id))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def get_owned_topic(db: Session, user_id: int, topic_id: int) -> Topic:
    topic = db.scalar(
        select(Topic)
        .join(Course, Topic.course_id == Course.id)
        .where(Topic.id == topic_id, Course.owner_id == user_id)
    )
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(
    payload: TopicCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TopicRead:
    get_owned_course(db, current_user.id, payload.course_id)
    topic = Topic(**payload.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicRead.model_validate(topic)


@router.get("", response_model=list[TopicRead])
def list_topics(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TopicRead]:
    get_owned_course(db, current_user.id, course_id)
    topics = db.scalars(select(Topic).where(Topic.course_id == course_id).order_by(Topic.id.desc())).all()
    return [TopicRead.model_validate(topic) for topic in topics]


@router.get("/{topic_id}", response_model=TopicRead)
def get_topic(
    topic_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TopicRead:
    topic = get_owned_topic(db, current_user.id, topic_id)
    return TopicRead.model_validate(topic)


@router.put("/{topic_id}", response_model=TopicRead)
def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TopicRead:
    topic = get_owned_topic(db, current_user.id, topic_id)
    for field, value in payload.model_dump().items():
        setattr(topic, field, value)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return TopicRead.model_validate(topic)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    topic = get_owned_topic(db, current_user.id, topic_id)
    db.execute(
        update(Note)
        .where(Note.user_id == current_user.id, Note.topic_id == topic.id)
        .values(topic_id=None)
    )
    db.delete(topic)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
