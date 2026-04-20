from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=2, max_length=2000)
    exam_date: date
    target_score: int = Field(ge=1, le=100)
    weekly_hours_goal: int = Field(ge=1, le=80)
    color_theme: str = Field(min_length=3, max_length=32)


class CourseUpdate(CourseCreate):
    pass


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    title: str
    description: str
    exam_date: date
    target_score: int
    weekly_hours_goal: int
    color_theme: str

