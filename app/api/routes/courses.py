from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.note import Note
from app.models.user import User
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate


router = APIRouter(prefix="/api/courses", tags=["courses"])


def get_owned_course(db: Session, user_id: int, course_id: int) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user_id))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CourseRead:
    course = Course(owner_id=current_user.id, **payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseRead.model_validate(course)


@router.get("", response_model=list[CourseRead])
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CourseRead]:
    courses = db.scalars(select(Course).where(Course.owner_id == current_user.id).order_by(Course.id.desc())).all()
    return [CourseRead.model_validate(course) for course in courses]


@router.get("/{course_id}", response_model=CourseRead)
def get_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CourseRead:
    course = get_owned_course(db, current_user.id, course_id)
    return CourseRead.model_validate(course)


@router.put("/{course_id}", response_model=CourseRead)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CourseRead:
    course = get_owned_course(db, current_user.id, course_id)
    for field, value in payload.model_dump().items():
        setattr(course, field, value)
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseRead.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    course = get_owned_course(db, current_user.id, course_id)
    db.execute(
        update(Note)
        .where(Note.user_id == current_user.id, Note.course_id == course.id)
        .values(course_id=None, topic_id=None)
    )
    db.delete(course)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
