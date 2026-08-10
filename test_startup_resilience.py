"""
Startup resilience tests.

Regression coverage for a production outage: a paused Supabase project made the
database unreachable, `models.Base.metadata.create_all(bind=engine)` ran at
import time in main.py, the import raised OperationalError, uvicorn exited, and
systemd restarted the service 189,072 times.

The app must start and stay up when the database is unreachable, reporting the
condition through /health rather than dying.
"""

import importlib
import sys

import pytest
from fastapi.testclient import TestClient

# A routable-but-dead address: connection attempts fail fast rather than hanging.
UNREACHABLE_DB = "postgresql://user:pw@127.0.0.1:59999/postgres"


def _load_app(monkeypatch, database_url):
    """Import main.py fresh with the given DATABASE_URL, returning the module."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    # providers.get_vision_provider() raises without a key; supply a dummy so
    # these tests exercise database behaviour only.
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-not-used")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("API_KEY", "test-api-key")

    for mod in ("main", "database", "models"):
        sys.modules.pop(mod, None)

    return importlib.import_module("main")


def test_app_imports_when_database_unreachable(monkeypatch):
    """The import must not raise when the database cannot be reached.

    This is the exact failure that caused the outage.
    """
    main = _load_app(monkeypatch, UNREACHABLE_DB)
    assert main.app is not None


def test_root_endpoint_serves_when_database_unreachable(monkeypatch):
    """Liveness must not depend on the database."""
    main = _load_app(monkeypatch, UNREACHABLE_DB)
    with TestClient(main.app) as client:
        response = client.get("/")
    assert response.status_code == 200


def test_health_reports_503_when_database_unreachable(monkeypatch):
    """/health must signal degraded state with a non-200 code."""
    main = _load_app(monkeypatch, UNREACHABLE_DB)
    with TestClient(main.app) as client:
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["database"] == "down"


def test_health_reports_200_when_database_reachable(monkeypatch, tmp_path):
    """/health must report healthy against a working database."""
    db_file = tmp_path / "health.db"
    main = _load_app(monkeypatch, f"sqlite:///{db_file}")
    with TestClient(main.app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "up"
