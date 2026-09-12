# Overnight 2026-09-11 — WhatsApp human-approval gate

Data: 11 de setembro de 2026

## Objetivo

Impedir que agentes de IA / automações (Lex, prazos, financeiro) **enviem
WhatsApp ao cliente sem aprovação humana** — prática recomendada 2026 para
SaaS jurídico e compliance de comunicação.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `OutboundMessageApproval` em `backend/database.py` |
| Tabela | `outbound_message_approvals` |
| Campos | id, user_id, channel (`whatsapp`), recipient, body, status (`pending\|approved\|rejected\|sent\|failed`), source (`lex\|deadline\|finance\|manual`), related_matter_id, created_at, decided_at, error |
| Service | `backend/services/outbound_approval_service.py` — `queue_whatsapp_for_approval`, `try_send_whatsapp` |
| Rotas | `backend/routes/approvals_routes.py` — JWT + rate limit |
| Registro | `app.include_router(approvals_router)` em `main.py` |

Endpoints:

- `GET /approvals/outbound?status=pending` — lista (default pending)
- `POST /approvals/outbound` — cria pending
- `POST /approvals/outbound/{id}/approve` — aprova; tenta Twilio/Evolution se configurado; senão `approved` com nota simulada
- `POST /approvals/outbound/{id}/reject` — rejeita (não envia)

### Frontend

- Página trust-shell: `frontend/app/dashboard/approvals/page.tsx`
- Lista pendentes com **Aprovar** / **Rejeitar**
- Link em Ações Rápidas do dashboard: **Aprovações WhatsApp**
- sim-real documenta o path de produção (enqueue → gate humano)

### Testes

- `backend/tests/test_approvals_routes.py` — create/list, approve simulado,
  reject, double-approve 409, IDOR 404, auth, helper queue, source inválido
- App mínimo com `TestClient` (sem importar `main`); **8/8 passed**

## Decisões de desenho

1. **Gate obrigatório para automação** — `queue_whatsapp_for_approval` nunca
   envia; só cria `pending`. Finance/deadline/Lex passam a usar o helper.
2. **Approve tenta send real** — se `WhatsAppConfig` ativo + Twilio/Evolution
   OK → `sent`; senão `approved` + nota “simulado” (dev/demo sem credenciais).
3. **Ownership por `user_id`** — multi-tenant simples; IDOR retorna 404.
4. **sim-real não chama API** — permanece demo visual; texto aponta o path
   de produção e a UI `/dashboard/approvals`.
5. **Canal único neste MVP** — `whatsapp` apenas; extensível depois.

## Como validar

```bash
cd backend
pytest tests/test_approvals_routes.py -q
```

UI: login → Dashboard → **Aprovações WhatsApp** → criar via API/POST →
Aprovar/Rejeitar.

```bash
# Exemplo criar pending (com JWT)
curl -X POST http://127.0.0.1:8000/approvals/outbound \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"recipient":"11999998888","body":"Teste gate","source":"manual"}'
```

## Próximos passos (fora deste MVP)

- Wire deadline reminders e cobrança financeira no helper (remover auto-send)
- Notificação in-app / badge de pendentes no dashboard
- Audit log de approve/reject com ator
- Template preview + edição antes de aprovar
