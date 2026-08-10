"""
Keepalive tests.

Supabase pauses Free plan projects after ~7 days of low database activity, which took
/bad-core/ down on 2026-08-10. A daily systemd timer writes a single row to keep the
project active; /health surfaces when that last happened so a dead timer is discoverable.
"""

import importlib
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

UNREACHABLE_DB = "postgresql://user:pw@127.0.0.1:59999/postgres"


def _load(monkeypatch, database_url):
    """Import the app modules fresh against the given DATABASE_URL."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-used")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("API_KEY", "test-api-key")

    for mod in ("main", "database", "models", "keepalive"):
        sys.modules.pop(mod, None)

    database = importlib.import_module("database")
    models = importlib.import_module("models")
    keepalive = importlib.import_module("keepalive")
    models.Base.metadata.create_all(bind=database.engine)
    return database, models, keepalive


def test_first_run_creates_the_keepalive_row(monkeypatch, tmp_path):
    database, models, keepalive = _load(monkeypatch, f"sqlite:///{tmp_path/'k.db'}")

    assert keepalive.main() == 0

    with database.SessionLocal() as session:
        rows = session.query(models.Keepalive).all()
    assert len(rows) == 1
    assert rows[0].last_ping is not None


def test_second_run_updates_rather_than_duplicating(monkeypatch, tmp_path):
    database, models, keepalive = _load(monkeypatch, f"sqlite:///{tmp_path/'k.db'}")

    keepalive.main()
    with database.SessionLocal() as session:
        first = session.query(models.Keepalive).one().last_ping

    keepalive.main()
    with database.SessionLocal() as session:
        rows = session.query(models.Keepalive).all()

    assert len(rows) == 1, "keepalive must hold exactly one row, never accumulate"
    assert rows[0].last_ping >= first


def _load_keepalive_only(monkeypatch, database_url):
    """Import keepalive without pre-creating schema (the DB is unreachable)."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-used")
    monkeypatch.setenv("API_KEY", "test-api-key")
    for mod in ("main", "database", "models", "keepalive"):
        sys.modules.pop(mod, None)
    return importlib.import_module("keepalive")


def test_keepalive_returns_nonzero_when_database_unreachable(monkeypatch):
    """systemd must see a failed run, so the exit code has to be non-zero."""
    keepalive = _load_keepalive_only(monkeypatch, UNREACHABLE_DB)
    assert keepalive.main() != 0


def test_health_reports_fresh_keepalive(monkeypatch, tmp_path):
    database, models, keepalive = _load(monkeypatch, f"sqlite:///{tmp_path/'k.db'}")
    keepalive.main()

    main = importlib.import_module("main")
    with TestClient(main.app) as client:
        body = client.get("/health").json()

    assert body["keepalive"]["stale"] is False
    assert body["keepalive"]["last_ping"] is not None


def test_health_reports_stale_keepalive_past_threshold(monkeypatch, tmp_path):
    database, models, keepalive = _load(monkeypatch, f"sqlite:///{tmp_path/'k.db'}")

    stale_at = datetime.now(timezone.utc) - timedelta(hours=72)
    with database.SessionLocal() as session:
        session.add(models.Keepalive(id=1, last_ping=stale_at))
        session.commit()

    main = importlib.import_module("main")
    with TestClient(main.app) as client:
        body = client.get("/health").json()

    assert body["keepalive"]["stale"] is True


def test_health_handles_never_pinged(monkeypatch, tmp_path):
    _load(monkeypatch, f"sqlite:///{tmp_path/'k.db'}")

    main = importlib.import_module("main")
    with TestClient(main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200, "a missing ping is not a service failure"
    assert response.json()["keepalive"]["last_ping"] is None
    assert response.json()["keepalive"]["stale"] is True
