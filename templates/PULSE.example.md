# Cortex Pulse Monitor Checklist

This checklist is read periodically by `scripts/pulse.py` with zero LLM token consumption.
Local notifications and logs trigger only when thresholds are breached.

## Automated Thresholds
- `disk_warn_pct`: 90
- `ram_avail_min_mb`: 400
- `swap_warn_pct`: 85
- `cooldown_hours`: 4

## Monitored Services and Schedulers
- Windows Task Scheduler (`CortexPulse`) or Linux systemd user timer (`agy-pulse.timer`)
- Local database or development daemons (optional)

## Proactive Tasks and Reminders
- [ ] Daily memory sync across mounted workspaces
- [ ] Weekly review of indexed decisions and project progress
