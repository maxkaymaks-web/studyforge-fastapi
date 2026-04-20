from datetime import date, datetime, time, timedelta
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.course import Course
from app.models.mentor_comment import MentorComment
from app.models.note import Note
from app.models.note_folder import NoteFolder
from app.models.quiz_attempt import QuizAttempt
from app.models.study_session import StudySession
from app.models.topic import Topic
from app.models.user import User


DEMO_EMAIL = "demo@studyforge.app"
DEMO_MENTOR_EMAIL = "mentor.demo@studyforge.app"


class DemoSeedResult(NamedTuple):
    email: str
    course_titles: list[str]


def _at(day: date, hour: int) -> datetime:
    return datetime.combine(day, time(hour=hour))


def _ensure_user(db: Session, *, email: str, full_name: str, role: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    password_hash = get_password_hash(password)
    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            password_hash=password_hash,
        )
        db.add(user)
        db.flush()
        return user
    user.full_name = full_name
    user.role = role
    user.password_hash = password_hash
    db.flush()
    return user


def seed_demo_account(db: Session, *, password: str, today: date | None = None) -> DemoSeedResult:
    current_day = today or date.today()
    mentor = _ensure_user(
        db,
        email=DEMO_MENTOR_EMAIL,
        full_name="Demo Mentor",
        role="mentor",
        password=password,
    )
    demo_user = _ensure_user(
        db,
        email=DEMO_EMAIL,
        full_name="Demo Student",
        role="student",
        password=password,
    )

    existing_notes = db.scalars(select(Note).where(Note.user_id == demo_user.id)).all()
    for note in existing_notes:
        db.delete(note)
    existing_folders = db.scalars(select(NoteFolder).where(NoteFolder.user_id == demo_user.id)).all()
    for folder in existing_folders:
        db.delete(folder)
    existing_courses = db.scalars(select(Course).where(Course.owner_id == demo_user.id)).all()
    for course in existing_courses:
        db.delete(course)
    db.flush()

    genomics = Course(
        owner_id=demo_user.id,
        title="Computational Genomics Sprint",
        description="Подготовка к экзамену по анализу геномных данных с акцентом на практические пайплайны.",
        exam_date=current_day + timedelta(days=16),
        target_score=92,
        weekly_hours_goal=11,
        color_theme="emerald",
    )
    signals = Course(
        owner_id=demo_user.id,
        title="Biomedical Signal Analysis",
        description="Курс по обработке биомедицинских сигналов, фильтрации и спектральному анализу.",
        exam_date=current_day + timedelta(days=29),
        target_score=88,
        weekly_hours_goal=9,
        color_theme="amber",
    )
    db.add_all([genomics, signals])
    db.flush()

    topics = [
        Topic(
            course_id=genomics.id,
            title="Variant Calling",
            description="Пайплайн от raw reads до confident variants.",
            difficulty=5,
            importance=5,
            estimated_minutes=170,
            mastery_level=42,
            last_reviewed_at=_at(current_day - timedelta(days=4), 11),
            status="in_progress",
        ),
        Topic(
            course_id=genomics.id,
            title="RNA-seq Differential Expression",
            description="Нормализация, модель шума и интерпретация логарифмических fold-change.",
            difficulty=4,
            importance=5,
            estimated_minutes=140,
            mastery_level=67,
            last_reviewed_at=_at(current_day - timedelta(days=2), 15),
            status="review",
        ),
        Topic(
            course_id=genomics.id,
            title="Genome Assembly",
            description="Основы de novo assembly и оценка качества сборки.",
            difficulty=5,
            importance=4,
            estimated_minutes=180,
            mastery_level=28,
            last_reviewed_at=None,
            status="planned",
        ),
        Topic(
            course_id=signals.id,
            title="ECG Preprocessing",
            description="Удаление шумов, baseline wander и подготовка сигнала к анализу.",
            difficulty=3,
            importance=4,
            estimated_minutes=110,
            mastery_level=74,
            last_reviewed_at=_at(current_day - timedelta(days=1), 10),
            status="done",
        ),
        Topic(
            course_id=signals.id,
            title="Spectral Analysis",
            description="FFT, PSD и выбор окна для частотного анализа.",
            difficulty=4,
            importance=5,
            estimated_minutes=135,
            mastery_level=51,
            last_reviewed_at=_at(current_day - timedelta(days=5), 16),
            status="in_progress",
        ),
        Topic(
            course_id=signals.id,
            title="Wavelet Features",
            description="Time-frequency decomposition и извлечение устойчивых признаков.",
            difficulty=5,
            importance=4,
            estimated_minutes=155,
            mastery_level=33,
            last_reviewed_at=None,
            status="planned",
        ),
    ]
    db.add_all(topics)
    db.flush()

    topics_by_title = {topic.title: topic for topic in topics}

    folders = [
        NoteFolder(user_id=demo_user.id, name="Учёба"),
        NoteFolder(user_id=demo_user.id, name="Быстрые заметки"),
        NoteFolder(user_id=demo_user.id, name="Идеи"),
    ]
    db.add_all(folders)
    db.flush()

    folders_by_name = {folder.name: folder for folder in folders}

    sessions = [
        StudySession(
            topic_id=topics_by_title["Variant Calling"].id,
            user_id=demo_user.id,
            planned_for=current_day - timedelta(days=3),
            actual_minutes=95,
            focus_score=8,
            notes="Разобрал best practices по фильтрации ложноположительных вариантов.",
        ),
        StudySession(
            topic_id=topics_by_title["RNA-seq Differential Expression"].id,
            user_id=demo_user.id,
            planned_for=current_day - timedelta(days=1),
            actual_minutes=70,
            focus_score=7,
            notes="Сверил edgeR и DESeq2 на учебном наборе данных.",
        ),
        StudySession(
            topic_id=topics_by_title["Genome Assembly"].id,
            user_id=demo_user.id,
            planned_for=current_day,
            actual_minutes=80,
            focus_score=6,
            notes="Прошёлся по метрикам N50 и coverage gaps.",
        ),
        StudySession(
            topic_id=topics_by_title["ECG Preprocessing"].id,
            user_id=demo_user.id,
            planned_for=current_day - timedelta(days=4),
            actual_minutes=60,
            focus_score=8,
            notes="Повторил band-pass filtering и нормировку амплитуды.",
        ),
        StudySession(
            topic_id=topics_by_title["Spectral Analysis"].id,
            user_id=demo_user.id,
            planned_for=current_day - timedelta(days=2),
            actual_minutes=85,
            focus_score=7,
            notes="Сравнил поведение Hann и Hamming окна на ECG-сигнале.",
        ),
        StudySession(
            topic_id=topics_by_title["Wavelet Features"].id,
            user_id=demo_user.id,
            planned_for=current_day,
            actual_minutes=75,
            focus_score=6,
            notes="Составил шпаргалку по выбору wavelet family для классификации аритмий.",
        ),
    ]
    db.add_all(sessions)

    quizzes = [
        QuizAttempt(topic_id=topics_by_title["Variant Calling"].id, user_id=demo_user.id, score=36, max_score=50),
        QuizAttempt(topic_id=topics_by_title["RNA-seq Differential Expression"].id, user_id=demo_user.id, score=41, max_score=50),
        QuizAttempt(topic_id=topics_by_title["Genome Assembly"].id, user_id=demo_user.id, score=18, max_score=40),
        QuizAttempt(topic_id=topics_by_title["ECG Preprocessing"].id, user_id=demo_user.id, score=27, max_score=30),
        QuizAttempt(topic_id=topics_by_title["Spectral Analysis"].id, user_id=demo_user.id, score=31, max_score=45),
        QuizAttempt(topic_id=topics_by_title["Wavelet Features"].id, user_id=demo_user.id, score=21, max_score=40),
    ]
    db.add_all(quizzes)

    comments = [
        MentorComment(
            course_id=genomics.id,
            author_id=mentor.id,
            body="Сфокусируйтесь на Variant Calling и Genome Assembly: именно там сейчас максимальный риск для защиты.",
        ),
        MentorComment(
            course_id=genomics.id,
            author_id=mentor.id,
            body="После каждой практической сессии фиксируйте, какой шаг пайплайна даётся медленнее всего.",
        ),
        MentorComment(
            course_id=signals.id,
            author_id=mentor.id,
            body="Для Signal Analysis уже виден прогресс, но Wavelet Features пока требует отдельного блока повторения.",
        ),
    ]
    db.add_all(comments)

    notes = [
        Note(
            user_id=demo_user.id,
            folder_id=folders_by_name["Учёба"].id,
            course_id=genomics.id,
            topic_id=topics_by_title["Variant Calling"].id,
            title="Чек-лист по Variant Calling",
            body="- [ ] ещё раз пройти pipeline\n- [ ] проверить hard filtering\n- [x] сравнить GATK и bcftools",
            color_tone="sunny",
            is_pinned=True,
        ),
        Note(
            user_id=demo_user.id,
            folder_id=folders_by_name["Учёба"].id,
            course_id=genomics.id,
            topic_id=topics_by_title["Genome Assembly"].id,
            title="Genome Assembly: что спросить на защите",
            body="Собрать короткие ответы по N50, coverage gaps, contig/scaffold distinction и quality metrics.",
            color_tone="lavender",
            is_pinned=False,
        ),
        Note(
            user_id=demo_user.id,
            folder_id=folders_by_name["Быстрые заметки"].id,
            course_id=signals.id,
            topic_id=topics_by_title["Wavelet Features"].id,
            title="Wavelet family cheat sheet",
            body="Для ECG-кейсов сравнить Daubechies и Symlets. Сразу выписать, где лучше ловятся аритмии.",
            color_tone="mint",
            is_pinned=True,
        ),
        Note(
            user_id=demo_user.id,
            folder_id=folders_by_name["Идеи"].id,
            title="Идея для видео-защиты",
            body=(
                "Показать сначала панель с прогрессом, потом аналитику курса, "
                "затем планировщик и раздел заметок как личную базу знаний."
            ),
            color_tone="rose",
            is_pinned=False,
        ),
    ]
    db.add_all(notes)

    db.commit()
    return DemoSeedResult(
        email=DEMO_EMAIL,
        course_titles=[genomics.title, signals.title],
    )
