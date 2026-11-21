# OpenClaw-Style Heartbeat Checklist

This checklist is read periodically by `scripts/heartbeat.py` with zero LLM token consumption.
Local notifications and alerts trigger only when thresholds are breached.

## Automated Thresholds
- `disk_warn_pct`: 90
- `ram_avail_min_mb`: 400
- `swap_warn_pct`: 85
- `cooldown_hours`: 4

## Monitored Services & Schedulers
- Windows Task Scheduler (`AntigravityHeartbeat`) or Linux systemd timer (`agy-heartbeat.timer`)
- Critical network or database daemons

## Proactive Tasks & Reminders
- [ ] Daily memory sync across mounted workspaces
- [ ] Weekly review of indexed decisions and project progress
