from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    app_name: str
    app_env: str
    secret_key: str
    access_token_expire_minutes: int
    database_url: str


def _default_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/studyforge.db"
    return "sqlite:///./studyforge.db"


def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "StudyForge"),
        app_env=os.getenv("APP_ENV", "development"),
        secret_key=os.getenv("SECRET_KEY", "change-me"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120")),
        database_url=_default_database_url(),
    )
