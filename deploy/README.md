# Deployment units

systemd units for the VPS (`103.179.56.61`). Kept in the repo so the deployed
configuration is version-controlled rather than hand-edited on the box.

## Supabase keepalive

Supabase pauses Free plan projects after roughly 7 days of low database activity. A daily
write keeps the project active. See [`../keepalive.py`](../keepalive.py) and
[the design note](../docs/superpowers/specs/2026-08-10-supabase-keepalive-design.md).

Install:

```bash
sudo cp deploy/bad-core-keepalive.service deploy/bad-core-keepalive.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bad-core-keepalive.timer
```

Verify:

```bash
systemctl list-timers bad-core-keepalive.timer
sudo systemctl start bad-core-keepalive.service   # force one run
journalctl -u bad-core-keepalive -n 20
curl -s https://app.dioriza.com/bad-core/health
```

`/health` reports when the keepalive last ran, and flags `stale` once the last ping is
over 48 hours old:

```json
{ "status": "ok", "database": "up",
  "keepalive": { "last_ping": "2026-08-10T06:30:00+00:00", "stale": false } }
```

A stale keepalive does **not** change the HTTP status code — the service is healthy; the
staleness is a warning that the project may pause.

> The timer runs on the VPS, so a VPS outage lasting over a week means the project pauses
> anyway with nothing to announce it. The `stale` flag is what makes that discoverable.
