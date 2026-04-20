from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.comments import router as comments_router
from app.api.routes.courses import router as courses_router
from app.api.routes.note_folders import router as note_folders_router
from app.api.routes.notes import router as notes_router
from app.api.routes.planner import router as planner_router
from app.api.routes.quizzes import router as quizzes_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.topics import router as topics_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(comments_router)
api_router.include_router(courses_router)
api_router.include_router(note_folders_router)
api_router.include_router(notes_router)
api_router.include_router(planner_router)
api_router.include_router(quizzes_router)
api_router.include_router(sessions_router)
api_router.include_router(topics_router)
