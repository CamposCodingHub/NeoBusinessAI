# Overnight 2026-09-11 — `datetime.utcnow()` → UTC-aware

Scoped fix only (no codebase-wide refactor).

## Changed
- **Routes:** `intake_routes.py`, `matter_routes.py`, `approvals_routes.py` — assignments use `datetime.now(timezone.utc)`.
- **Models (new overnight only):** `Lead`, `Matter`, `TimeEntry`, `OutboundMessageApproval` defaults/onupdate → `lambda: datetime.now(timezone.utc)`.
- **Auth:** `create_access_token` / `create_refresh_token` `iat`/`exp` → aware UTC.
- **Memory timestamps:** `premium_conversational_engine.py` conversation message timestamps.

## Skipped (no `utcnow` / out of scope)
- `time_routes.py`, `chat_memory_service.py` — no direct `utcnow` usage.
- Older `database.py` models and unrelated services left on `datetime.utcnow`.

## SQLite note
Aware values are written via SQLAlchemy `DateTime` (no `timezone=True`); SQLite continues to store/compare naive UTC wall times, so existing naive DB comparisons stay safe.

## Tests
`38 passed` (venv311) for intake / matter / approvals / time / chat_memory.
Remaining `utcnow` DeprecationWarnings come from older models (User etc.), intentionally untouched.
