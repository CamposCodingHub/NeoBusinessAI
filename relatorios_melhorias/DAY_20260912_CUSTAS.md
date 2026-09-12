# DAY 2026-09-12 — Custas / cost advances

## Goal
Track court cost advances (guias, perícia, diligências) with reimburse / write-off status for lawyer & accountant workflows.

## Deliverables

| Path | Role |
|------|------|
| `CostAdvance` model in `backend/database.py` | id, user_id, client_id?, matter_id?, description, amount, status, created_at |
| `CRUD /finance/cost-advances` | JWT ownership |
| `frontend/app/dashboard/finance/page.tsx` | Custas section |
| `backend/tests/test_finance_cost_advances.py` | ≥3 tests |

## Status values
- `advanced` — paid by firm, awaiting client
- `reimbursed` — client repaid
- `written_off` — absorbed / waived with justification outside system

## Endpoints
- `GET /finance/cost-advances` — list (`?status=&client_id=&matter_id=`)
- `POST /finance/cost-advances` — create
- `GET /finance/cost-advances/{id}`
- `PATCH /finance/cost-advances/{id}`
- `DELETE /finance/cost-advances/{id}`

## Tests
```bash
cd backend
python -m pytest tests/test_finance_cost_advances.py -q
```

## Not in scope
Bank sync, automatic invoice generation from advances, multi-currency.
