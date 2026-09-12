# DAY 2026-09-12 — Sim Real + Lex ops shortcuts (tick 9)

## Goal
Keep `/sim-real` as the daytime demo of newer modules without overcrowding the rail, and expose Lex ops shortcuts for engagement / firm ops.

## Deliverables

| Path | Change |
|------|--------|
| `frontend/app/sim-real/page.tsx` | Restored (was empty dir) + 2 phases (`firm`, `monitor`) + finance aging/NFS-e + WA consent events |
| `backend/routes/operations_routes.py` | `GET /operations/shortcuts` adds engagement, orgs, trust, esign, monitor, finance |
| `backend/scripts/run_full_qa_simulator.py` | Auth POST smoke: `/deadlines/compute-business` |
| `frontend/app/globals.css` | Appended TRUST shell tokens/utilities if missing (no wipe of existing neon block) |

## Sim-real phases (new / folded)

- **firm** — Org + Trust + E-Sign (3 timeline events, one rail chip)
- **monitor** — intimação monitor + engagement feed note
- **finance** — existing faturas + aging + NFS-e stub events
- **whatsapp** — consent check + approval enqueue (approval phase restored in cycle)

## Validate

```bash
cd backend
python -m pytest tests/test_operations_intelligence.py tests/test_activity_feed.py -q
python scripts/run_professional_domain_eval.py
```

Open `/sim-real` — rail shows Firm / Monitor; event log includes aging, NFS-e, consent.

## Not in scope
Commit, Playwright rewrite, real prefeitura/Twilio calls.
