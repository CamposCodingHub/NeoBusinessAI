# Overnight 2026-09-12 — Payment link stub (PIX/Stripe path)

Data: 12 de setembro de 2026

## Objetivo

Dar o próximo passo pragmático após Time → Invoice e Portal: **gerar e persistir
um link de pagamento por fatura**, com Stripe quando configurado e stub local
assinado (`pay.lexscan.local`) no caminho típico de desenvolvimento BR (futuro PIX).

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `Invoice.payment_url` (VARCHAR 1024, nullable) em `backend/database.py` |
| Migração SQLite | `_apply_sqlite_development_migrations` adiciona `invoices.payment_url` |
| Endpoint | `POST /finance/invoices/{id}/payment-link` (JWT, owner only) |
| Stripe | `StripeManager.create_invoice_checkout_session` (one-time BRL) se `STRIPE_SECRET_KEY` |
| Stub | `https://pay.lexscan.local/i/{id}?token={random}.{hmac16}` — token em `payment_reference` |
| Portal | `_serialize_invoice` inclui `payment_url` |

Resposta:

```json
{ "payment_url": "https://...", "provider": "stripe"|"stub", "invoice_id": 1 }
```

Segurança:

- Filtro `Invoice.user_id == current_user.id` (404 se IDOR / inexistente)
- Fatura `cancelled` → 400
- Client email só lido se `Client.user_id` bater com o dono

### Frontend

- `frontend/app/portal/page.tsx`: link **Pagar** quando `payment_url` presente e
  status ≠ paid/cancelled.

### Testes

- `backend/tests/test_invoice_payment_link.py` — ≥4 casos:
  - stub gera URL + persiste
  - IDOR 404 (outro user) sem gravar URL
  - auth obrigatória
  - cancelled → 400
  - portal lista `payment_url`

## Decisões de desenho

1. **Coluna `payment_url`** — explícita vs JSON; fácil de listar no portal.
2. **Stub primeiro** — Stripe opcional; escritórios BR vão para PIX depois.
3. **Token HMAC curto** — não é gateway real; só amarra o link ao invoice_id.
4. **Sem botão no finance dashboard** — geração via API; cliente vê “Pagar” no portal.

## Como validar

```bash
cd backend
pytest tests/test_invoice_payment_link.py -q
```

Fluxo manual: criar fatura → `POST /finance/invoices/{id}/payment-link` → portal
do cliente mostra **Pagar**.

## Próximos passos (fora deste MVP)

- Página real `pay.lexscan` / QR PIX (Mercado Pago ou Stripe BR)
- Webhook marca fatura `paid`
- Botão “Gerar link” no dashboard financeiro do escritório
- Expiração / regeneração de token
