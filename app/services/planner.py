import csv
from datetime import UTC, date, datetime, timedelta
from io import StringIO
from typing import NamedTuple

from app.models.course import Course
from app.models.quiz_attempt import QuizAttempt
from app.models.topic import Topic
from app.schemas.planner import StudyPlanRecommendation, StudyPlanResponse, StudyPlanSummary


class RankedTopic(NamedTuple):
    topic: Topic
    priority_score: float
    reason: str


def latest_quiz_ratios(attempts: list[QuizAttempt]) -> dict[int, float]:
    ratios: dict[int, float] = {}
    for attempt in attempts:
        if attempt.topic_id not in ratios:
            ratios[attempt.topic_id] = attempt.score / attempt.max_score
    return ratios


def compute_priority(course: Course, topic: Topic, today: date, quiz_ratio: float | None) -> RankedTopic:
    days_until_exam = max((course.exam_date - today).days, 1)
    days_since_review = 14 if topic.last_reviewed_at is None else max((today - topic.last_reviewed_at.date()).days, 0)
    knowledge_gap_weight = (100 - topic.mastery_level) * 0.9
    forgetting_weight = min(days_since_review, 30) * 1.8
    importance_weight = topic.importance * 12
    difficulty_weight = topic.difficulty * 7
    urgency_weight = max(0, 21 - days_until_exam) * 2.5
    quiz_gap_weight = 12 if quiz_ratio is None else (1 - quiz_ratio) * 30
    status_weight = 10 if topic.status in {"planned", "in_progress"} else 2
    priority_score = (
        knowledge_gap_weight
        + forgetting_weight
        + importance_weight
        + difficulty_weight
        + urgency_weight
        + quiz_gap_weight
        + status_weight
    )
    quiz_context = "самопроверка ещё не пройдена" if quiz_ratio is None else f"самопроверка {round(quiz_ratio * 100)}%"
    reason = (
        f"освоение {topic.mastery_level}%, важность {topic.importance}/5, "
        f"{quiz_context}, последнее повторение {days_since_review} дн. назад"
    )
    return RankedTopic(topic=topic, priority_score=round(priority_score, 2), reason=reason)


def build_study_plan(
    course: Course,
    topics: list[Topic],
    attempts: list[QuizAttempt] | None = None,
    days: int = 5,
    today: date | None = None,
) -> StudyPlanResponse:
    plan_day = today or date.today()
    attempt_list = attempts or []
    ratios = latest_quiz_ratios(attempt_list)
    ranked_topics = sorted(
        [compute_priority(course, topic, plan_day, ratios.get(topic.id)) for topic in topics],
        key=lambda item: item.priority_score,
        reverse=True,
    )

    if not ranked_topics:
        return StudyPlanResponse(
            course_id=course.id,
            course_title=course.title,
            generated_at=datetime.now(UTC),
            recommendations=[],
            summary=StudyPlanSummary(
                total_recommended_minutes=0,
                total_recommendations=0,
                average_daily_minutes=0,
                days_until_exam=max((course.exam_date - plan_day).days, 0),
                exam_date=course.exam_date,
            ),
        )

    total_available_minutes = max(60, round(course.weekly_hours_goal * 60 * (days / 7)))
    daily_budget = max(30, round(total_available_minutes / days))
    recommendations: list[StudyPlanRecommendation] = []

    for index in range(days):
        ranked_topic = ranked_topics[index % len(ranked_topics)]
        recommended_minutes = min(max(30, daily_budget), ranked_topic.topic.estimated_minutes)
        recommendations.append(
            StudyPlanRecommendation(
                planned_for=plan_day + timedelta(days=index),
                topic_id=ranked_topic.topic.id,
                topic_title=ranked_topic.topic.title,
                recommended_minutes=recommended_minutes,
                priority_score=ranked_topic.priority_score,
                reason=ranked_topic.reason,
            )
        )

    total_minutes = sum(item.recommended_minutes for item in recommendations)
    average_daily_minutes = round(total_minutes / len(recommendations)) if recommendations else 0
    return StudyPlanResponse(
        course_id=course.id,
        course_title=course.title,
        generated_at=datetime.now(UTC),
        recommendations=recommendations,
        summary=StudyPlanSummary(
            total_recommended_minutes=total_minutes,
            total_recommendations=len(recommendations),
            average_daily_minutes=average_daily_minutes,
            days_until_exam=max((course.exam_date - plan_day).days, 0),
            exam_date=course.exam_date,
        ),
    )


def render_study_plan_csv(plan: StudyPlanResponse) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["planned_for", "topic_title", "recommended_minutes", "priority_score", "reason"])
    for item in plan.recommendations:
        writer.writerow(
            [
                item.planned_for.isoformat(),
                item.topic_title,
                item.recommended_minutes,
                item.priority_score,
                item.reason,
            ]
        )
    return buffer.getvalue()
