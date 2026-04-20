from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.mentor_comment import MentorComment
    from app.models.note import Note
    from app.models.topic import Topic
    from app.models.user import User


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    exam_date: Mapped[date] = mapped_column(Date)
    target_score: Mapped[int] = mapped_column(Integer)
    weekly_hours_goal: Mapped[int] = mapped_column(Integer)
    color_theme: Mapped[str] = mapped_column(String(32), default="emerald")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="courses")
    notes: Mapped[list["Note"]] = relationship(back_populates="course")
    topics: Mapped[list["Topic"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    mentor_comments: Mapped[list["MentorComment"]] = relationship(back_populates="course", cascade="all, delete-orphan")
