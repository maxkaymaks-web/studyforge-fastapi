from collections import Counter
from datetime import date, timedelta
from typing import NamedTuple

from app.models.course import Course
from app.models.quiz_attempt import QuizAttempt
from app.models.study_session import StudySession
from app.models.topic import Topic
from app.schemas.planner import StudyPlanRecommendation, StudyPlanResponse
from app.services.planner import build_study_plan, compute_priority, latest_quiz_ratios


STATUS_LABELS = {
    "planned": "Запланировано",
    "in_progress": "В процессе",
    "review": "Повторение",
    "done": "Завершено",
}


class CourseSnapshot(NamedTuple):
    course_id: int
    title: str
    color_theme: str
    exam_date: date
    days_until_exam: int
    readiness_percent: int
    average_mastery: float
    average_quiz_percent: int
    weak_topics_count: int
    total_study_minutes: int
    next_focus_topic_title: str | None
    readiness_tone: str
    readiness_label: str


class DashboardFocusRecommendation(NamedTuple):
    course_id: int
    course_title: str
    topic_id: int
    topic_title: str
    planned_for: date
    recommended_minutes: int
    priority_score: float
    reason: str


class DashboardCriticalTopic(NamedTuple):
    course_id: int
    course_title: str
    topic_id: int
    topic_title: str
    mastery_level: int
    days_until_exam: int
    priority_score: float


class DashboardLoadPoint(NamedTuple):
    label: str
    minutes: int
    height_percent: int
    is_today: bool


class DashboardTrendPoint(NamedTuple):
    label: str
    value: int
    height_percent: int


class AchievementBadge(NamedTuple):
    title: str
    description: str
    tone: str


class DeadlineInsight(NamedTuple):
    course_id: int
    course_title: str
    exam_date: date
    days_until_exam: int
    readiness_percent: int
    tone: str


class CourseRiskInsight(NamedTuple):
    course_id: int
    course_title: str
    risk_score: int
    readiness_percent: int
    weak_topics_count: int
    days_until_exam: int
    tone: str


class DashboardInsights(NamedTuple):
    course_snapshots: list[CourseSnapshot]
    focus_today: DashboardFocusRecommendation | None
    critical_topics: list[DashboardCriticalTopic]
    streak_days: int
    health_score: int
    health_label: str
    health_tone: str
    weekly_load: list[DashboardLoadPoint]
    quiz_trend: list[DashboardTrendPoint]
    achievements: list[AchievementBadge]
    upcoming_deadlines: list[DeadlineInsight]
    course_risks: list[CourseRiskInsight]


class StatusDistributionSlice(NamedTuple):
    label: str
    count: int
    percent: int
    tone: str


class CourseBlocker(NamedTuple):
    title: str
    detail: str
    tone: str


class CourseIntelligence(NamedTuple):
    status_distribution: list[StatusDistributionSlice]
    recent_quiz_trend: list[DashboardTrendPoint]
    blockers: list[CourseBlocker]
    next_action_title: str
    next_action_description: str
    next_action_href: str


class PlannerLoadPoint(NamedTuple):
    label: str
    minutes: int
    height_percent: int
    topic_title: str


class PlannerVisualization(NamedTuple):
    daily_load: list[PlannerLoadPoint]
    projected_readiness_percent: int
    projected_delta: int
    projected_readiness_label: str
    projected_readiness_tone: str


def _sorted_attempts(attempts: list[QuizAttempt]) -> list[QuizAttempt]:
    return sorted(attempts, key=lambda item: item.attempted_at, reverse=True)


def _average_quiz_percent(attempts: list[QuizAttempt]) -> int:
    ratios = latest_quiz_ratios(_sorted_attempts(attempts))
    if not ratios:
        return 0
    return round(sum(ratios.values()) / len(ratios) * 100)


def _readiness_badge(readiness_percent: int, days_until_exam: int) -> tuple[str, str]:
    if readiness_percent < 45 or (days_until_exam <= 7 and readiness_percent < 65):
        return "risk", "Риск"
    if readiness_percent < 70:
        return "attention", "Нужна фокусировка"
    return "good", "Под контролем"


def _series_height(value: int, max_value: int) -> int:
    if max_value <= 0:
        return 16
    return max(16, round(value / max_value * 100))


def _short_date(day: date) -> str:
    return day.strftime("%d.%m")


def _streak_days(sessions: list[StudySession], today: date) -> int:
    session_days = {session.planned_for for session in sessions if session.planned_for <= today}
    streak = 0
    cursor = today
    while cursor in session_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _weekly_load(sessions: list[StudySession], today: date) -> list[DashboardLoadPoint]:
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    totals = {
        day: sum(session.actual_minutes for session in sessions if session.planned_for == day)
        for day in days
    }
    max_minutes = max(totals.values(), default=0)
    return [
        DashboardLoadPoint(
            label=_short_date(day),
            minutes=totals[day],
            height_percent=_series_height(totals[day], max_minutes),
            is_today=day == today,
        )
        for day in days
    ]


def _quiz_trend(attempts: list[QuizAttempt], limit: int = 6) -> list[DashboardTrendPoint]:
    recent_attempts = sorted(attempts, key=lambda item: item.attempted_at)[-limit:]
    values = [round(attempt.score / attempt.max_score * 100) for attempt in recent_attempts]
    max_value = max(values, default=0)
    return [
        DashboardTrendPoint(
            label=attempt.attempted_at.strftime("%d.%m"),
            value=round(attempt.score / attempt.max_score * 100),
            height_percent=_series_height(round(attempt.score / attempt.max_score * 100), max_value),
        )
        for attempt in recent_attempts
    ]


def _achievement_badges(
    streak_days: int,
    total_quizzes: int,
    total_minutes: int,
    average_readiness: int,
) -> list[AchievementBadge]:
    achievements: list[AchievementBadge] = []
    if streak_days >= 3:
        achievements.append(
            AchievementBadge(
                title=f"{streak_days} дня подряд" if streak_days < 5 else f"{streak_days} дней подряд",
                description="Выдержан устойчивый ритм занятий.",
                tone="good",
            )
        )
    if total_quizzes >= 3:
        achievements.append(
            AchievementBadge(
                title="Самопроверка в ритме",
                description="Есть достаточная история результатов для анализа прогресса.",
                tone="attention",
            )
        )
    if total_minutes >= 240:
        achievements.append(
            AchievementBadge(
                title="Хорошая нагрузка недели",
                description="Накоплен заметный объём учебного времени.",
                tone="good",
            )
        )
    if average_readiness >= 70:
        achievements.append(
            AchievementBadge(
                title="Курсы под контролем",
                description="Средняя готовность уже вышла в уверенную зону.",
                tone="good",
            )
        )
    return achievements[:3]


def _course_risk(snapshot: CourseSnapshot) -> CourseRiskInsight:
    urgency_penalty = max(0, 14 - snapshot.days_until_exam) * 3
    risk_score = min(100, max(0, (100 - snapshot.readiness_percent) + snapshot.weak_topics_count * 6 + urgency_penalty))
    return CourseRiskInsight(
        course_id=snapshot.course_id,
        course_title=snapshot.title,
        risk_score=risk_score,
        readiness_percent=snapshot.readiness_percent,
        weak_topics_count=snapshot.weak_topics_count,
        days_until_exam=snapshot.days_until_exam,
        tone=snapshot.readiness_tone,
    )


def build_course_snapshot(
    course: Course,
    topics: list[Topic],
    attempts: list[QuizAttempt],
    sessions: list[StudySession],
    today: date | None = None,
) -> CourseSnapshot:
    current_day = today or date.today()
    days_until_exam = max((course.exam_date - current_day).days, 0)
    average_mastery = round(sum(topic.mastery_level for topic in topics) / len(topics), 1) if topics else 0.0
    average_quiz_percent = _average_quiz_percent(attempts)
    total_study_minutes = sum(session.actual_minutes for session in sessions)
    weak_topics_count = sum(1 for topic in topics if topic.mastery_level < 60 or topic.status != "done")
    baseline_quiz_percent = average_quiz_percent or round(average_mastery)
    activity_bonus = min(total_study_minutes / max(course.weekly_hours_goal * 60, 1), 1) * 10
    urgency_penalty = 8 if days_until_exam <= 7 else 4 if days_until_exam <= 14 else 0
    raw_readiness = average_mastery * 0.55 + baseline_quiz_percent * 0.35 + activity_bonus - urgency_penalty
    readiness_percent = max(0, min(100, round(raw_readiness)))
    readiness_tone, readiness_label = _readiness_badge(readiness_percent, days_until_exam)
    next_focus_topic_title = None
    if topics:
        focus_plan = build_study_plan(course=course, topics=topics, attempts=attempts, days=1, today=current_day)
        if focus_plan.recommendations:
            next_focus_topic_title = focus_plan.recommendations[0].topic_title

    return CourseSnapshot(
        course_id=course.id,
        title=course.title,
        color_theme=course.color_theme,
        exam_date=course.exam_date,
        days_until_exam=days_until_exam,
        readiness_percent=readiness_percent,
        average_mastery=average_mastery,
        average_quiz_percent=average_quiz_percent,
        weak_topics_count=weak_topics_count,
        total_study_minutes=total_study_minutes,
        next_focus_topic_title=next_focus_topic_title,
        readiness_tone=readiness_tone,
        readiness_label=readiness_label,
    )


def build_dashboard_insights(
    courses: list[Course],
    topics: list[Topic],
    attempts: list[QuizAttempt],
    sessions: list[StudySession],
    today: date | None = None,
) -> DashboardInsights:
    current_day = today or date.today()
    topics_by_course: dict[int, list[Topic]] = {course.id: [] for course in courses}
    for topic in topics:
        topics_by_course.setdefault(topic.course_id, []).append(topic)

    topic_to_course = {topic.id: topic.course_id for topic in topics}
    attempts_by_course: dict[int, list[QuizAttempt]] = {course.id: [] for course in courses}
    for attempt in attempts:
        course_id = topic_to_course.get(attempt.topic_id)
        if course_id is not None:
            attempts_by_course.setdefault(course_id, []).append(attempt)

    sessions_by_course: dict[int, list[StudySession]] = {course.id: [] for course in courses}
    for session in sessions:
        course_id = topic_to_course.get(session.topic_id)
        if course_id is not None:
            sessions_by_course.setdefault(course_id, []).append(session)

    snapshots: list[CourseSnapshot] = []
    focus_candidates: list[DashboardFocusRecommendation] = []
    critical_topics: list[DashboardCriticalTopic] = []

    for course in courses:
        course_topics = topics_by_course.get(course.id, [])
        course_attempts = attempts_by_course.get(course.id, [])
        course_sessions = sessions_by_course.get(course.id, [])
        snapshot = build_course_snapshot(
            course=course,
            topics=course_topics,
            attempts=course_attempts,
            sessions=course_sessions,
            today=current_day,
        )
        snapshots.append(snapshot)

        if course_topics:
            focus_plan = build_study_plan(
                course=course,
                topics=course_topics,
                attempts=course_attempts,
                days=1,
                today=current_day,
            )
            if focus_plan.recommendations:
                recommendation: StudyPlanRecommendation = focus_plan.recommendations[0]
                focus_candidates.append(
                    DashboardFocusRecommendation(
                        course_id=course.id,
                        course_title=course.title,
                        topic_id=recommendation.topic_id,
                        topic_title=recommendation.topic_title,
                        planned_for=recommendation.planned_for,
                        recommended_minutes=recommendation.recommended_minutes,
                        priority_score=recommendation.priority_score,
                        reason=recommendation.reason,
                    )
                )

            ratios = latest_quiz_ratios(_sorted_attempts(course_attempts))
            for topic in course_topics:
                ranked_topic = compute_priority(course, topic, current_day, ratios.get(topic.id))
                critical_topics.append(
                    DashboardCriticalTopic(
                        course_id=course.id,
                        course_title=course.title,
                        topic_id=topic.id,
                        topic_title=topic.title,
                        mastery_level=topic.mastery_level,
                        days_until_exam=snapshot.days_until_exam,
                        priority_score=ranked_topic.priority_score,
                    )
                )

    snapshots.sort(key=lambda item: (item.days_until_exam, item.readiness_percent))
    focus_today = max(focus_candidates, key=lambda item: item.priority_score, default=None)
    critical_topics.sort(key=lambda item: item.priority_score, reverse=True)

    streak_days = _streak_days(sessions, current_day)
    weekly_load = _weekly_load(sessions, current_day)
    quiz_trend = _quiz_trend(attempts)
    average_readiness = round(sum(snapshot.readiness_percent for snapshot in snapshots) / len(snapshots)) if snapshots else 0
    average_quiz_percent = round(sum(point.value for point in quiz_trend) / len(quiz_trend)) if quiz_trend else average_readiness
    weekly_minutes = sum(point.minutes for point in weekly_load)
    consistency_score = min(100, round((weekly_minutes / 420) * 100)) if weekly_minutes else 0
    health_score = max(
        0,
        min(
            100,
            round(
                average_readiness * 0.55
                + average_quiz_percent * 0.2
                + consistency_score * 0.15
                + min(streak_days * 6, 10)
            ),
        ),
    )
    health_tone, health_label = _readiness_badge(
        health_score,
        min((snapshot.days_until_exam for snapshot in snapshots), default=21),
    )
    achievements = _achievement_badges(
        streak_days=streak_days,
        total_quizzes=len(attempts),
        total_minutes=weekly_minutes,
        average_readiness=average_readiness,
    )
    upcoming_deadlines = [
        DeadlineInsight(
            course_id=snapshot.course_id,
            course_title=snapshot.title,
            exam_date=snapshot.exam_date,
            days_until_exam=snapshot.days_until_exam,
            readiness_percent=snapshot.readiness_percent,
            tone=snapshot.readiness_tone,
        )
        for snapshot in snapshots[:4]
    ]
    course_risks = sorted((_course_risk(snapshot) for snapshot in snapshots), key=lambda item: item.risk_score, reverse=True)[:4]

    return DashboardInsights(
        course_snapshots=snapshots,
        focus_today=focus_today,
        critical_topics=critical_topics[:4],
        streak_days=streak_days,
        health_score=health_score,
        health_label=health_label,
        health_tone=health_tone,
        weekly_load=weekly_load,
        quiz_trend=quiz_trend,
        achievements=achievements,
        upcoming_deadlines=upcoming_deadlines,
        course_risks=course_risks,
    )


def build_course_intelligence(
    course: Course,
    topics: list[Topic],
    attempts: list[QuizAttempt],
    sessions: list[StudySession],
    today: date | None = None,
) -> CourseIntelligence:
    current_day = today or date.today()
    snapshot = build_course_snapshot(course=course, topics=topics, attempts=attempts, sessions=sessions, today=current_day)
    status_counts = Counter(topic.status for topic in topics)
    total_topics = len(topics) or 1
    status_distribution = [
        StatusDistributionSlice(
            label=STATUS_LABELS[status_key],
            count=status_counts.get(status_key, 0),
            percent=round(status_counts.get(status_key, 0) / total_topics * 100),
            tone="good" if status_key == "done" else "attention" if status_key == "review" else "risk",
        )
        for status_key in ("planned", "in_progress", "review", "done")
    ]
    recent_quiz_trend = _quiz_trend(attempts)

    blockers: list[CourseBlocker] = []
    weak_topics = sum(1 for topic in topics if topic.mastery_level < 60)
    if weak_topics:
        blockers.append(
            CourseBlocker(
                title="Слабые темы тормозят готовность",
                detail=f"{weak_topics} тем ещё не дошли до уверенного уровня освоения.",
                tone="risk",
            )
        )
    if snapshot.average_quiz_percent and snapshot.average_quiz_percent < course.target_score - 15:
        blockers.append(
            CourseBlocker(
                title="Самопроверка пока ниже цели",
                detail=f"Средний результат {snapshot.average_quiz_percent}% против цели {course.target_score}%.",
                tone="attention",
            )
        )
    recent_minutes = sum(session.actual_minutes for session in sessions if session.planned_for >= current_day - timedelta(days=6))
    if recent_minutes < course.weekly_hours_goal * 60 * 0.6:
        blockers.append(
            CourseBlocker(
                title="Недельная нагрузка ниже плана",
                detail=f"За последние 7 дней набрано {recent_minutes} мин при цели {course.weekly_hours_goal * 60} мин.",
                tone="attention",
            )
        )
    if not blockers:
        blockers.append(
            CourseBlocker(
                title="Курс движется ровно",
                detail="Ключевых ограничений не видно, можно удерживать текущий темп.",
                tone="good",
            )
        )

    focus_topic = snapshot.next_focus_topic_title or "следующий учебный блок"
    return CourseIntelligence(
        status_distribution=status_distribution,
        recent_quiz_trend=recent_quiz_trend,
        blockers=blockers,
        next_action_title="Обновить план курса",
        next_action_description=f"Следующий логичный шаг — пересчитать план и закрепить фокус на теме «{focus_topic}».",
        next_action_href=f"/planner/{course.id}",
    )


def build_planner_visualization(plan: StudyPlanResponse, snapshot: CourseSnapshot) -> PlannerVisualization:
    minutes = [item.recommended_minutes for item in plan.recommendations]
    max_minutes = max(minutes, default=0)
    daily_load = [
        PlannerLoadPoint(
            label=item.planned_for.strftime("%d.%m"),
            minutes=item.recommended_minutes,
            height_percent=_series_height(item.recommended_minutes, max_minutes),
            topic_title=item.topic_title,
        )
        for item in plan.recommendations
    ]
    readiness_gain = min(18, round(plan.summary.total_recommended_minutes / max(plan.summary.total_recommendations, 1) / 18))
    projected_readiness_percent = min(100, snapshot.readiness_percent + readiness_gain)
    projected_delta = projected_readiness_percent - snapshot.readiness_percent
    projected_readiness_tone, projected_readiness_label = _readiness_badge(
        projected_readiness_percent,
        plan.summary.days_until_exam,
    )
    return PlannerVisualization(
        daily_load=daily_load,
        projected_readiness_percent=projected_readiness_percent,
        projected_delta=projected_delta,
        projected_readiness_label=projected_readiness_label,
        projected_readiness_tone=projected_readiness_tone,
    )
