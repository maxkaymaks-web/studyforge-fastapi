from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    body: str = Field(min_length=2, max_length=8000)
    folder_id: int | None = None
    course_id: int | None = None
    topic_id: int | None = None
    color_tone: str = Field(min_length=3, max_length=32)
    is_pinned: bool = False


class NoteUpdate(NoteCreate):
    pass


class NoteListFilters(BaseModel):
    folder_id: int | None = None
    course_id: int | None = None
    topic_id: int | None = None
    pinned: bool | None = None
    q: str | None = Field(default=None, max_length=255)


class NotesPageFilters(BaseModel):
    folder_id: int | None = None
    note_id: int | None = None
    course_id: int | None = None
    q: str | None = Field(default=None, max_length=255)


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    folder_id: int | None
    course_id: int | None
    topic_id: int | None
    title: str
    body: str
    color_tone: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
