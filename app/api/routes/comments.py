from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.mentor_comment import MentorComment
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead


router = APIRouter(prefix="/api/comments", tags=["comments"])


def get_course(db: Session, course_id: int) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id))
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def get_comment(db: Session, comment_id: int) -> MentorComment:
    comment = db.scalar(select(MentorComment).where(MentorComment.id == comment_id))
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    payload: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CommentRead:
    if current_user.role != "mentor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only mentors can add comments")
    course = get_course(db, payload.course_id)
    comment = MentorComment(course_id=course.id, author_id=current_user.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentRead.model_validate(comment)


@router.get("", response_model=list[CommentRead])
def list_comments(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CommentRead]:
    course = get_course(db, course_id)
    if current_user.role != "mentor" and course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    comments = db.scalars(
        select(MentorComment).where(MentorComment.course_id == course_id).order_by(MentorComment.id.desc())
    ).all()
    return [CommentRead.model_validate(comment) for comment in comments]


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    comment = get_comment(db, comment_id)
    course = get_course(db, comment.course_id)
    if current_user.role != "mentor" and course.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if current_user.role == "mentor" and comment.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete another mentor comment")
    db.delete(comment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

