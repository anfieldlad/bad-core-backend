# Supabase keepalive — design

Date: 2026-08-10

## Problem

Supabase pauses Free plan projects after roughly 7 days of low activity. When that
happened on 2026-08-10 the pooler deregistered the tenant, every connection failed with
`ENOTFOUND tenant/user`, and `/bad-core/` returned 502 until the project was resumed
manually from the dashboard.

The inactivity timer tracks **database** activity — not dashboard visits. A periodic
query or write resets it. Supabase's own wording is vague ("low activity in a 7-day
period"), and reports of success centre on **writes** rather than reads, so this design
uses a write.

The application was separately hardened (commit `4b97dab`) so an outage degrades the
service instead of crash-looping. This keepalive addresses the cause rather than the
symptom: keeping the project from pausing in the first place.

## Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Where it runs | systemd timer on the VPS | Self-contained; credentials already present in `.env`; no third party |
| What it does | Single-row upsert | A write is the signal reported to work; one row never grows |
| Cadence | Daily | 7-day window ⇒ 7× buffer, tolerates six consecutive failures |
| Visibility | `last_ping` surfaced in `/health` | Reuses an endpoint that already exists |
| Stale threshold | 48 h | Double the cadence: tolerates one miss, exposes a dead timer |
| Stale ⇒ HTTP code | Stays 200 | The service really is healthy; a stale ping is future risk, not current fault. Encoding it as 503 would misreport a working service, and cry wolf once real monitoring exists. |

**Accepted limitation:** the keepalive lives on the VPS, so a VPS outage lasting over a
week means the project pauses anyway with nothing to announce it. That was chosen
deliberately over an external pinger to avoid a third-party dependency. The `stale` flag
in `/health` is what makes the failure discoverable after the fact.

## Components

**`keepalive.py`** — standalone script, run by systemd. Imports the engine from
`database.py`, so `DATABASE_URL` and `pool_pre_ping` are not duplicated. Calls
`create_all` itself (idempotent) so it works even if the web app has never started.
Returns exit code 0 on success, 1 on failure, so systemd records a failed run.

**`models.Keepalive`** — one table, one row:

```python
class Keepalive(Base):
    __tablename__ = "keepalive"
    id = Column(Integer, primary_key=True)              # always 1
    last_ping = Column(DateTime(timezone=True), nullable=False)
```

Upsert is a plain ORM get-or-create rather than a Postgres `ON CONFLICT`, keeping the
code path identical under sqlite so tests exercise the real logic. Safe without locking:
one writer, once a day.

**`/health`** gains a `keepalive` block:

```json
{ "status": "ok", "database": "up",
  "keepalive": { "last_ping": "2026-08-10T06:30:00+00:00", "stale": false } }
```

Omitted when the database is unreachable, since the row cannot be read. `last_ping: null`
with `stale: true` when no ping has ever been recorded.

sqlite does not preserve timezone information, so a naive `last_ping` read back from the
database is coerced to UTC before comparison.

**systemd units**

```ini
# bad-core-keepalive.service
[Service]
Type=oneshot
User=dioriza
WorkingDirectory=/opt/bad-core-backend
EnvironmentFile=/opt/bad-core-backend/.env
ExecStart=/opt/bad-core-backend/.venv/bin/python keepalive.py
```

```ini
# bad-core-keepalive.timer
[Timer]
OnCalendar=daily
RandomizedDelaySec=1h
Persistent=true
```

`Persistent=true` runs a missed ping once the machine is back, instead of waiting for the
next scheduled point — the difference between recovering from a reboot and silently
skipping a day.

## Tests

Written before implementation:

1. First run creates the keepalive row
2. Second run updates that row rather than inserting another
3. `/health` reports `last_ping` and `stale: false` after a fresh ping
4. `/health` reports `stale: true` when the last ping is older than 48 h
5. `/health` handles no ping ever having been recorded
6. `keepalive.main()` returns a non-zero exit code when the database is unreachable

## Out of scope

- Alerting on a stale keepalive (a monitor's job, not the status code's)
- Pruning: not applicable, the table holds one row
- The same treatment for the other three services: none has an external database
