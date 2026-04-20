from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.database import SessionLocal, init_db
from app.services.demo_seed import seed_demo_account
from app.web import router as web_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    if os.getenv("VERCEL"):
        db = SessionLocal()
        try:
            seed_demo_account(db, password=os.getenv("DEMO_PASSWORD", "DemoPreview123!"))
        finally:
            db.close()
    yield


app = FastAPI(title="StudyForge", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")
app.include_router(api_router)
app.include_router(web_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
