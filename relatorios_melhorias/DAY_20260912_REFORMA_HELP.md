# DAY 2026-09-12 — Reforma Tributária / eSocial–DCTFWeb help (accountant)

## Goal
Methodological Contador help for Reforma Tributária and eSocial × EFD-Reinf × DCTFWeb pain — **no invented tax rates**, **no exact legal due dates as facts**, **no article numbers asserted as certainty**.

## Deliverables

| Path | Role |
|------|------|
| `frontend/app/ajuda/page.tsx` | Contador tab: checklist **Reforma / eSocial × DCTFWeb** + anchor `#reforma-esocial`; link from tax-calendar section |
| `backend/services/tax_reform_checklist_service.py` | Static checklist JSON builder |
| `GET /finance/tax-reform-checklist` | JWT; same methodological content for API consumers |
| `frontend/app/dashboard/finance/page.tsx` | Tax-calendar section link → `/ajuda#reforma-esocial` |
| `backend/tests/test_finance_tax_reform_checklist.py` | JWT + static shape + no fake rates/days/arts |
| `DAY_20260912_REFORMA_HELP.md` | This note |

## Checklist themes (UI + API)
1. **Cruzamento eSocial × EFD-Reinf × DCTFWeb** — conferir consistência S-1200/S-1210 (método)
2. **Reforma** — apuração paralela / campos IBS-CBS em NF (confirmar calendário oficial vigente)
3. **Disclaimer** — LexScan auxilia; contador CRC valida; legislação muda

## Response shape
```json
{
  "items": [
    {
      "id": "esocial_reinf_dctfweb",
      "title": "Cruzamento eSocial × EFD-Reinf × DCTFWeb",
      "summary": "…",
      "steps": ["…"],
      "method_note": "…"
    },
    {
      "id": "reforma_ibs_cbs",
      "title": "Reforma Tributária — apuração paralela / IBS-CBS em NF",
      "summary": "…",
      "steps": ["…"],
      "method_note": "…"
    },
    {
      "id": "disclaimer_crc",
      "title": "Papel do LexScan vs. contador CRC",
      "summary": "LexScan auxilia; contador CRC valida; legislação muda.",
      "steps": ["…"],
      "method_note": "…"
    }
  ],
  "count": 3,
  "disclaimer": "LexScan auxilia…",
  "stub": true,
  "source": "methodological_help_not_legal_advice"
}
```

Missing JWT → 401/403.

## Tests
```bash
cd backend
python -m pytest tests/test_finance_tax_reform_checklist.py -q
```

## Not in scope
RFB integration, invented aliquotas, fixed due-day tables, article-number certainty, auto-filing, replacing CRC sign-off.
