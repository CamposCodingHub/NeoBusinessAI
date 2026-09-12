# Overnight 2026-09-12 — Time → Invoice (billing pragmático)

Data: 12 de setembro de 2026

## Objetivo

Fechar o próximo passo do Time Entry MVP: **criar fatura (draft/pending) a
partir de lançamentos de horas faturáveis**, com ownership JWT e marcação
`invoiced_at` para não faturar duas vezes.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `TimeEntry.invoiced_at` (DateTime nullable) em `backend/database.py` |
| Migração SQLite | `_apply_sqlite_development_migrations` adiciona `time_entries.invoiced_at` se a tabela já existir |
| Endpoint | `POST /time/entries/invoice` (JWT + rate limit) em `time_routes.py` |
| Invoice | Reutiliza model `Invoice` existente + `generate_invoice_number()` de `finance_routes` |

Body:

```json
{ "entry_ids": [1, 2], "client_id": null, "matter_id": null, "due_days": 7 }
```

Comportamento:

- Com `entry_ids`: só entries **billable**, **não faturadas**, do usuário; IDs
  ausentes / de outro user / já faturados → **404** (sem leak IDOR).
- Sem `entry_ids`: exige `client_id` e/ou `matter_id`; fatura todos uninvoiced
  billable do filtro (ownership validada).
- Total = `sum(minutes/60 * hourly_rate)`; entries sem taxa ou valor ≤ 0 são
  ignoradas no total.
- Cria `Invoice` com `status=pending`, `invoice_type=time_entries`,
  `total_cents` = total × 100; marca `invoiced_at` nos entries usados.
- `client_id` da fatura: do body, ou único client_id comum entre as entries.

### Frontend

- `frontend/app/dashboard/time/page.tsx`: checkboxes + botão
  **Faturar selecionados**; badge “faturado” quando `invoiced_at` preenchido.

### Testes

- `backend/tests/test_time_invoice.py` — ≥4 casos:
  - fatura por `entry_ids` + total + `invoiced_at`
  - ignora zero rate / rejeita mix com non-billable (404)
  - fatura por `client_id` (só uninvoiced) + segunda chamada 400
  - IDOR 404 + auth obrigatória + body vazio 400

## Decisões de desenho

1. **`invoiced_at` no TimeEntry** — mínimo invasivo vs JSON em Invoice.
2. **Endpoint em `/time`** — próximo do domínio de horas; Invoice continua no módulo financeiro.
3. **Status `pending`** — Invoice não tinha `draft`; pending = draft operacional.
4. **Strict entry_ids** — se qualquer ID pedido não for elegível, 404 (seguro multi-tenant).

## Como validar

```bash
cd backend
pytest tests/test_time_invoice.py -q
```

UI: Dashboard → Time Entries → selecionar linhas faturáveis → **Faturar selecionados**.

## Próximos passos (fora deste MVP)

- Endpoint espelho `POST /finance/invoices/from-time`
- PDF / envio da fatura
- Desfazer faturamento (clear `invoiced_at` + cancel invoice)
- Dropdown client/matter na UI de time
