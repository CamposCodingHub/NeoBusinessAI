# DAY 2026-09-12 — Ethical collection plan (régua de cobrança)

## Goal
Suggested ethical dunning steps for open invoices — D-3 / D0 / D+3 / D+7 — with EOAB disclaimer (no aggressive collection, no auto-send).

## Deliverables

| Path | Role |
|------|------|
| `backend/services/collection_plan_service.py` | Pure plan builder from invoice aging |
| `GET /finance/collection-plan` | JWT; optional `?invoice_id=` |
| `frontend/app/dashboard/finance/page.tsx` | Régua ética section |
| `backend/tests/test_finance_collection_plan.py` | ≥3 tests |

## Response shape
```json
{
  "plans": [
    {
      "invoice_id": 1,
      "days_from_due": 5,
      "recommended_step": "D+7",
      "steps": [
        {"code": "D-3", "label": "Lembrete pré-vencimento", "is_current": false},
        {"code": "D0", "label": "Vencimento", "is_current": false},
        {"code": "D+3", "label": "Cobrança gentil", "is_current": false},
        {"code": "D+7", "label": "Notificação formal", "is_current": true}
      ]
    }
  ],
  "count": 1,
  "disclaimer": "Régua ética (stub). Cobrança deve observar o Código de Ética…",
  "currency": "BRL"
}
```

Open = status `pending` or `overdue`. Planning only — does not send WhatsApp/e-mail.

## Tests
```bash
cd backend
python -m pytest tests/test_finance_collection_plan.py -q
```

## Not in scope
Automated sends, aggressive scripts, CollectionStep persistence table.
