# StudyForge

StudyForge is a FastAPI web application for planning exam preparation. It combines relational data management, JWT authentication, algorithmic study recommendations, and a clean demo-oriented interface.

## Why this project exists

Students often know what course they are preparing for, but they do not know what to study today. StudyForge solves that problem by combining:

- course and topic management;
- study session logging;
- quiz result tracking;
- mentor feedback;
- a planning algorithm that prioritizes topics by mastery gap, importance, time since review, and exam proximity.

The result is not just CRUD. It is a study planning service with a concrete business task and a visible algorithmic decision layer.

## Subject area

Scientific and educational domain: exam and course preparation planning.

## Main features

- JWT-based authentication with registration and login
- relational SQLite database with 6 connected entities
- CRUD for courses and topics
- activity tracking for study sessions and quiz attempts
- mentor comments with role-based restrictions
- planner endpoint that generates a multi-day study plan
- web interface for login, dashboard, course workspace, and planner view
- notes workspace with folders and course-linked study notes

## Data model

The application uses these main tables:

- `users`
- `courses`
- `topics`
- `study_sessions`
- `quiz_attempts`
- `mentor_comments`

Relationships:

- one user owns many courses;
- one course contains many topics;
- one topic has many study sessions;
- one topic has many quiz attempts;
- one course has many mentor comments.

## Business logic

The planner computes a priority score for each topic based on:

- low mastery level;
- high importance;
- high difficulty;
- long time since previous review;
- latest quiz performance;
- days remaining until the exam.

The `/api/planner/{course_id}` endpoint distributes available study time across the requested number of days and returns JSON recommendations with explanations.

## Tech stack

- Python 3.11
- FastAPI
- SQLAlchemy
- Jinja2 templates
- SQLite
- python-jose
- passlib
- pylint

## Repository structure

```text
app/
  api/
  core/
  models/
  schemas/
  services/
  static/
  templates/
  main.py
scripts/
requirements.txt
README.md
.env.example
pylint.txt
```

## Installation and run

1. Create a virtual environment:

```bash
python3.11 -m venv .venv
```

2. Install dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

3. Create environment file:

```bash
cp .env.example .env
```

4. Run the application:

```bash
.venv/bin/uvicorn app.main:app --reload
```

5. Open:

- App UI: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/docs`

SQLite database file is created automatically.

## Code quality

The repository includes a ready `pylint.txt` report for the published code snapshot.

## API overview

Authentication:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/token`
- `GET /api/auth/me`

Courses:

- `POST /api/courses`
- `GET /api/courses`
- `GET /api/courses/{course_id}`
- `PUT /api/courses/{course_id}`
- `DELETE /api/courses/{course_id}`

Topics:

- `POST /api/topics`
- `GET /api/topics`
- `GET /api/topics/{topic_id}`
- `PUT /api/topics/{topic_id}`
- `DELETE /api/topics/{topic_id}`

Study activity:

- `POST /api/sessions`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `PUT /api/sessions/{session_id}`
- `DELETE /api/sessions/{session_id}`
- `POST /api/quizzes`
- `GET /api/quizzes`
- `GET /api/quizzes/{attempt_id}`
- `PUT /api/quizzes/{attempt_id}`
- `DELETE /api/quizzes/{attempt_id}`

Mentor workflow:

- `POST /api/comments`
- `GET /api/comments`
- `DELETE /api/comments/{comment_id}`

Planner:

- `GET /api/planner/{course_id}`

## Web interface

The UI includes:

- landing page;
- login page;
- registration page;
- dashboard with key metrics and course creation form;
- course workspace with topic, session, and quiz forms;
- planner page with multi-day recommendations;
- notes page with folders and linked study notes.

## Demo

- Vercel deployment: `https://studyforge-oe4hlvhv3-iilyanaumov1998-5948s-projects.vercel.app`
- Demo account: `demo@studyforge.app`
- Demo password: `DemoPreview123!`

## Suggested video structure

Recommended 5-7 minute presentation flow:

1. Explain the problem: students need help deciding what to study next.
2. Show registration and login.
3. Show dashboard, course creation, and topic creation.
4. Show session and quiz logging on a course page.
5. Open the planner page and explain why certain topics are prioritized.
6. Open one backend file with the planning logic.
7. Run `pylint` and briefly comment on the result.

## Author

Maxim

## Delivery checklist

- repository with readable commit history
- `README.md`
- `requirements.txt`
- `.env.example`
- `pylint.txt`
- working FastAPI application
