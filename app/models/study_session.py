from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.topic import Topic
    from app.models.user import User


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    planned_for: Mapped[date] = mapped_column(Date)
    actual_minutes: Mapped[int] = mapped_column(Integer)
    focus_score: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    topic: Mapped["Topic"] = relationship(back_populates="study_sessions")
    user: Mapped["User"] = relationship(back_populates="study_sessions")

