from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.note_folder import NoteFolder
    from app.models.topic import Topic
    from app.models.user import User


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("note_folders.id"), index=True, nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), index=True, nullable=True)
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    color_tone: Mapped[str] = mapped_column(String(32), default="sunny")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="notes")
    folder: Mapped["NoteFolder | None"] = relationship(back_populates="notes")
    course: Mapped["Course | None"] = relationship(back_populates="notes")
    topic: Mapped["Topic | None"] = relationship(back_populates="notes")
