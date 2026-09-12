# DAY 2026-09-12 — Client profitability stub

## Goal
Pain point: lawyers don't know profit per client. JWT endpoint + compact finance UI for a rough operational estimate (not accounting).

## Deliverables

| Path | Role |
|------|------|
| `GET /finance/profitability` | JWT; per-client invoiced / time_value / costs_open / rough_margin |
| `frontend/app/dashboard/finance/page.tsx` | Compact trust-style table |
| `backend/tests/test_finance_profitability.py` | ≥3 tests |
| `relatorios_melhorias/DAY_20260912_PROFITABILITY.md` | This note |

## Response shape
```json
{
  "clients": [
    {
      "client_id": 1,
      "client_name": "Alpha Adv",
      "invoiced": 1500.0,
      "time_value": 300.0,
      "costs_open": 150.0,
      "rough_margin": 1350.0
    }
  ],
  "note": "estimativa operacional — nao e balanco contábil"
}
```

### Rules (best-effort)
- **invoiced**: sum of invoice `total_cents` with status `paid` or `pending`
- **time_value**: billable time × hourly_rate (minutes/60)
- **costs_open**: cost advances with status `advanced` (unreimbursed)
- **rough_margin**: `invoiced - costs_open` when invoiced > 0, else `time_value - costs_open`
- Soft-fail if models/fields missing; top N via `?limit=` (default 25)

## Tests
```bash
cd backend
python -m pytest tests/test_finance_profitability.py -q
```

## Not in scope
Full P&amp;L, overhead allocation, accrual accounting, multi-currency.
