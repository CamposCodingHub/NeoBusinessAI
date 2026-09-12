# DAY 2026-09-12 — Honorários antecipados / retainers

## Goal
Operational cash-flow tracking for lawyer retainers (honorários antecipados):
record advance fees, apply draws against remaining balance, surface status on finance dashboard.
No legal/ethics rules invented — balance bookkeeping only.

## Deliverables

| Path | Role |
|------|------|
| `FeeRetainer` model in `backend/database.py` | id, user_id, client_id, matter_id?, amount, amount_applied, status, notes, created_at |
| `POST/GET /finance/retainers` + `POST /finance/retainers/{id}/apply` | JWT ownership in `finance_routes.py` |
| `frontend/app/dashboard/finance/page.tsx` | Compact retainers section |
| `backend/tests/test_finance_retainers.py` | ≥4 tests |

## Status values
- `open` — nothing applied yet
- `partially_applied` — some balance used
- `exhausted` — fully applied (`remaining == 0`)
- `refunded` — reserved operational flag (apply blocked)

## Endpoints
- `GET /finance/retainers` — list (`?status=&client_id=&matter_id=`)
- `POST /finance/retainers` — create (`client_id` + `amount` required; `matter_id`/`notes` optional)
- `POST /finance/retainers/{id}/apply` — body `{ "amount": number }` reduces remaining

## Distinction vs CostAdvance
`CostAdvance` tracks court costs awaiting reimbursement.
`FeeRetainer` tracks prepaid fees / honorários antecipados with `amount_applied` balance.

## Tests
```bash
cd backend
python -m pytest tests/test_finance_retainers.py -q
```

## Not in scope
EOAB ethics automation, trust-account banking rules, invoice auto-generation from retainers, refund workflow UI.
