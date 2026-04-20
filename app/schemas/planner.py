from datetime import date, datetime

from pydantic import BaseModel


class StudyPlanRecommendation(BaseModel):
    planned_for: date
    topic_id: int
    topic_title: str
    recommended_minutes: int
    priority_score: float
    reason: str


class StudyPlanSummary(BaseModel):
    total_recommended_minutes: int
    total_recommendations: int
    average_daily_minutes: int
    days_until_exam: int
    exam_date: date


class StudyPlanResponse(BaseModel):
    course_id: int
    course_title: str
    generated_at: datetime
    recommendations: list[StudyPlanRecommendation]
    summary: StudyPlanSummary
