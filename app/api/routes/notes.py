from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.course import Course
from app.models.note import Note
from app.models.note_folder import NoteFolder
from app.models.topic import Topic
from app.models.user import User
from app.schemas.note import NoteCreate, NoteListFilters, NoteRead, NoteUpdate


router = APIRouter(prefix="/api/notes", tags=["notes"])


def get_owned_folder(db: Session, user_id: int, folder_id: int) -> NoteFolder:
    folder = db.scalar(select(NoteFolder).where(NoteFolder.id == folder_id, NoteFolder.user_id == user_id))
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder


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


def get_owned_note(db: Session, user_id: int, note_id: int) -> Note:
    note = db.scalar(select(Note).where(Note.id == note_id, Note.user_id == user_id))
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


def resolve_note_links(
    db: Session,
    user_id: int,
    payload: NoteCreate | NoteUpdate,
) -> tuple[int | None, int | None, int | None]:
    if payload.folder_id is not None:
        get_owned_folder(db, user_id, payload.folder_id)

    resolved_course_id = payload.course_id
    if payload.course_id is not None:
        get_owned_course(db, user_id, payload.course_id)

    resolved_topic_id = payload.topic_id
    if payload.topic_id is not None:
        topic = get_owned_topic(db, user_id, payload.topic_id)
        if resolved_course_id is not None and topic.course_id != resolved_course_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic does not belong to the selected course")
        resolved_course_id = topic.course_id
        resolved_topic_id = topic.id

    return payload.folder_id, resolved_course_id, resolved_topic_id


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NoteRead:
    folder_id, course_id, topic_id = resolve_note_links(db, current_user.id, payload)
    note = Note(
        user_id=current_user.id,
        title=payload.title,
        body=payload.body,
        folder_id=folder_id,
        course_id=course_id,
        topic_id=topic_id,
        color_tone=payload.color_tone,
        is_pinned=payload.is_pinned,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.get("", response_model=list[NoteRead])
def list_notes(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    filters: Annotated[NoteListFilters, Depends()],
) -> list[NoteRead]:
    query = select(Note).where(Note.user_id == current_user.id)
    if filters.folder_id is not None:
        get_owned_folder(db, current_user.id, filters.folder_id)
        query = query.where(Note.folder_id == filters.folder_id)
    if filters.course_id is not None:
        get_owned_course(db, current_user.id, filters.course_id)
        query = query.where(Note.course_id == filters.course_id)
    if filters.topic_id is not None:
        get_owned_topic(db, current_user.id, filters.topic_id)
        query = query.where(Note.topic_id == filters.topic_id)
    if filters.pinned is not None:
        query = query.where(Note.is_pinned == filters.pinned)
    if filters.q:
        pattern = f"%{filters.q.strip()}%"
        query = query.where(or_(Note.title.ilike(pattern), Note.body.ilike(pattern)))
    notes = db.scalars(query.order_by(Note.is_pinned.desc(), Note.updated_at.desc(), Note.id.desc())).all()
    return [NoteRead.model_validate(note) for note in notes]


@router.get("/{note_id}", response_model=NoteRead)
def get_note(
    note_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NoteRead:
    note = get_owned_note(db, current_user.id, note_id)
    return NoteRead.model_validate(note)


@router.put("/{note_id}", response_model=NoteRead)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NoteRead:
    note = get_owned_note(db, current_user.id, note_id)
    folder_id, course_id, topic_id = resolve_note_links(db, current_user.id, payload)
    note.title = payload.title
    note.body = payload.body
    note.folder_id = folder_id
    note.course_id = course_id
    note.topic_id = topic_id
    note.color_tone = payload.color_tone
    note.is_pinned = payload.is_pinned
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteRead.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    note = get_owned_note(db, current_user.id, note_id)
    db.delete(note)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
