"""
Keepalive ping for the Supabase Free plan.

Supabase pauses Free plan projects after roughly 7 days of low database activity. On
2026-08-10 that happened: the pooler deregistered the tenant and /bad-core/ returned 502
until the project was resumed by hand. The inactivity timer tracks database activity, and
a write resets it.

Run on a schedule by bad-core-keepalive.timer. Writes a single row (the table never
grows) and exits non-zero on failure so systemd records a failed run.

    python keepalive.py
"""

import sys
from datetime import datetime, timezone

from database import SessionLocal, engine
import models

# Single-row table: this id is the only one ever written.
KEEPALIVE_ROW_ID = 1


def record_ping(session, now=None):
    """Upsert the keepalive row and return the timestamp written.

    A plain get-or-create rather than a Postgres ON CONFLICT, so the same code path runs
    under sqlite in tests. Safe without locking: one writer, once a day.
    """
    now = now or datetime.now(timezone.utc)

    row = session.get(models.Keepalive, KEEPALIVE_ROW_ID)
    if row is None:
        session.add(models.Keepalive(id=KEEPALIVE_ROW_ID, last_ping=now))
    else:
        row.last_ping = now
    session.commit()

    return now


def main() -> int:
    """Write one keepalive ping. Returns a process exit code."""
    try:
        # Idempotent, and makes the script work even if the web app never started.
        models.Base.metadata.create_all(bind=engine)
        with SessionLocal() as session:
            stamp = record_ping(session)
    except Exception as exc:
        print(f"ERROR: keepalive failed: {exc}", file=sys.stderr)
        return 1

    print(f"OK: keepalive recorded at {stamp.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
