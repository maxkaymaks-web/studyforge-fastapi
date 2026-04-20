from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StudySessionBase(BaseModel):
    planned_for: date
    actual_minutes: int = Field(ge=0, le=720)
    focus_score: int = Field(ge=1, le=10)
    notes: str = Field(min_length=2, max_length=2000)


class StudySessionCreate(StudySessionBase):
    topic_id: int


class StudySessionUpdate(StudySessionBase):
    pass


class StudySessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    user_id: int
    planned_for: date
    actual_minutes: int
    focus_score: int
    notes: str
    created_at: datetime
