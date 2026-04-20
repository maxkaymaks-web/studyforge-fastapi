from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TopicCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=2, max_length=2000)
    difficulty: int = Field(ge=1, le=5)
    importance: int = Field(ge=1, le=5)
    estimated_minutes: int = Field(ge=15, le=1440)
    mastery_level: int = Field(ge=0, le=100)
    status: str = Field(pattern="^(planned|in_progress|review|done)$")


class TopicUpdate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=2, max_length=2000)
    difficulty: int = Field(ge=1, le=5)
    importance: int = Field(ge=1, le=5)
    estimated_minutes: int = Field(ge=15, le=1440)
    mastery_level: int = Field(ge=0, le=100)
    status: str = Field(pattern="^(planned|in_progress|review|done)$")


class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    description: str
    difficulty: int
    importance: int
    estimated_minutes: int
    mastery_level: int
    last_reviewed_at: datetime | None
    status: str
