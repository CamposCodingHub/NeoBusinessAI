# DAY 2026-09-12 — Playwright smoke CI skeleton

## Goal
Minimal e2e smoke that does not break default CI: skips when no frontend server is running; optional manual workflow only.

## Deliverables

| Path | Role |
|------|------|
| `frontend/tests/e2e/smoke.spec.ts` | Hits `/` or `/login`; expects visible title/heading; skips if unreachable |
| `frontend/package.json` | Script `test:e2e:smoke` |
| `.github/workflows/e2e-smoke.yml` | `workflow_dispatch` only |

## Run locally
```bash
cd frontend
# optional: npm run dev  (in another terminal)
npm run test:e2e:smoke
```

Without a server the spec **skips** (exit may still be 0 depending on Playwright skip handling).

## CI note
Workflow is manual (`workflow_dispatch`) and uses `continue-on-error: true` on the smoke step so an absent server does not red-badge the repo.
