# DAY_20260912 — WhatsApp LGPD consent stub + Lex trust chips

Data: 12 de setembro de 2026

## Objetivo

1. Polir chips de confiança no chat Lex quando a resposta premium traz metadados jurídicos.
2. Entregar stub de consentimento WhatsApp (LGPD) com gate soft no approve de outbound.

## A) Chat Lex metadata UI

Arquivo: `frontend/app/chat/page.tsx` (`LexMetaStrip`).

Chips compactos (navy/slate/teal) para:

| Campo | Quando mostra |
| --- | --- |
| `professional_domain` / `domains` | se presente (fallback `legal_area`) |
| `local_knowledge_hits` | se `> 0` |
| `official_sources_used` | códigos joined (até 4) |
| `response_mode` | se presente |

Também mantém docs internos / grounding / revisão humana no mesmo strip (sem UI duplicada).

Backend: `main.py` agora propaga `domains`, `professional_domains`, `local_knowledge_hits`, `official_sources_used` no metadata do `/api/chat/premium`.

## B) WhatsApp LGPD consent stub

### Model

`WhatsAppConsent` em `backend/database.py` (`whatsapp_consents`):

- `user_id`, `client_id` (nullable), `phone` / `phone_hash`
- `consented_at`, `channel=whatsapp`, `source` (`intake`|`manual`), `revoked_at` nullable

### Service / routes

- `services/whatsapp_consent_service.py` — grant / revoke / list / `has_active_consent`
- `routes/compliance_routes.py` (JWT):
  - `POST /compliance/whatsapp-consent`
  - `GET /compliance/whatsapp-consent?client_id=`
  - `POST /compliance/whatsapp-consent/revoke`
- Registrado em `main.py` (`compliance_router`)

### Soft gate no approvals

Em `POST /approvals/outbound/{id}/approve`, antes de `try_send_whatsapp`:

- se não houver consentimento ativo para o telefone do recipient → **403** com `code: WHATSAPP_CONSENT_REQUIRED`
- enqueue (`POST /approvals/outbound`) **não** é bloqueado (só o caminho de envio)

### Frontend (quick)

Seção mínima em `frontend/app/settings/page.tsx` — registrar consentimento por telefone.

### Testes

`backend/tests/test_whatsapp_consent.py` (≥4 casos):

1. create + list + revoke
2. GET filtrado por `client_id`
3. approve sem consent → 403 + código
4. approve com consent → 200 (approved/sent simulado)

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_whatsapp_consent.py -q
```

## Nota

Sem commit (pedido explícito). Arquivos de approvals **não** foram zerados — apenas patch do gate de consentimento.
