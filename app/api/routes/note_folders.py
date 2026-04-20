from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.note import Note
from app.models.note_folder import NoteFolder
from app.models.user import User
from app.schemas.note_folder import NoteFolderCreate, NoteFolderRead, NoteFolderUpdate


router = APIRouter(prefix="/api/note-folders", tags=["note-folders"])


def get_owned_folder(db: Session, user_id: int, folder_id: int) -> NoteFolder:
    folder = db.scalar(select(NoteFolder).where(NoteFolder.id == folder_id, NoteFolder.user_id == user_id))
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder


@router.post("", response_model=NoteFolderRead, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: NoteFolderCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NoteFolderRead:
    folder = NoteFolder(user_id=current_user.id, **payload.model_dump())
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return NoteFolderRead.model_validate(folder)


@router.get("", response_model=list[NoteFolderRead])
def list_folders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[NoteFolderRead]:
    folders = db.scalars(
        select(NoteFolder).where(NoteFolder.user_id == current_user.id).order_by(NoteFolder.name.asc())
    ).all()
    return [NoteFolderRead.model_validate(folder) for folder in folders]


@router.put("/{folder_id}", response_model=NoteFolderRead)
def update_folder(
    folder_id: int,
    payload: NoteFolderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> NoteFolderRead:
    folder = get_owned_folder(db, current_user.id, folder_id)
    folder.name = payload.name
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return NoteFolderRead.model_validate(folder)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    folder = get_owned_folder(db, current_user.id, folder_id)
    db.execute(
        update(Note)
        .where(Note.user_id == current_user.id, Note.folder_id == folder.id)
        .values(folder_id=None)
    )
    db.delete(folder)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
