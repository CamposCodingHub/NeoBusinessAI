# DAY 2026-09-12 — Tax calendar (accountant monthly obligations stub)

## Goal
Methodological monthly obligations reminder for accountants — **not** a real RFB / municipal calendar API. No invented tax rates or exact statutory due days.

## Deliverables

| Path | Role |
|------|------|
| `backend/services/tax_calendar_service.py` | Reminder builder + YYYY-MM validation |
| `GET /finance/tax-calendar?month=YYYY-MM` | JWT; list of methodological items |
| `frontend/app/dashboard/finance/page.tsx` | Calendário fiscal (stub) section |
| `frontend/app/ajuda/page.tsx` | Contador tab note + link |
| `backend/tests/test_finance_tax_calendar.py` | ≥2 tests |
| `DAY_20260912_TAX_CALENDAR.md` | This note |

## Response shape
```json
{
  "month": "2026-09",
  "items": [
    {
      "code": "SIMPLES_DAS",
      "title": "Simples Nacional / DAS",
      "due_hint": "2026-09: … confirmar calendário RFB/prefeitura vigente",
      "disclaimer": "…"
    },
    {
      "code": "ISS_MUNICIPAL",
      "title": "ISS municipal",
      "due_hint": "…",
      "disclaimer": "…"
    },
    {
      "code": "DCTFWEB_ESOCIAL",
      "title": "DCTFWeb / eSocial (eventos)",
      "due_hint": "…",
      "disclaimer": "…"
    }
  ],
  "count": 3,
  "disclaimer": "Lembretes metodológicos (stub)…",
  "stub": true,
  "source": "methodological_stub_not_rfb_api"
}
```

Invalid `month` → HTTP 400. Missing JWT → 401/403.

## Tests
```bash
cd backend
python -m pytest tests/test_finance_tax_calendar.py -q
```

## Not in scope
RFB SOAP/REST integration, municipal ISS APIs, aliquotas, fixed due-day tables, auto-filing.
