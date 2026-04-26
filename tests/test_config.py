from app.core.config import _default_database_url


def test_default_database_url_uses_local_sqlite(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)

    assert _default_database_url() == "sqlite:///./studyforge.db"


def test_default_database_url_uses_tmp_sqlite_on_vercel(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("VERCEL", "1")

    assert _default_database_url() == "sqlite:////tmp/studyforge.db"


def test_default_database_url_prefers_explicit_database_url(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")

    assert _default_database_url() == "postgresql://example"
