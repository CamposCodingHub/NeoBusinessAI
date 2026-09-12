# Overnight 2026-09-11 — Time Entry MVP (market gap: billable hours / PMS)

Data: 11 de setembro de 2026

## Objetivo

Fechar o gap de **lançamento de horas faturáveis (Time Entry)** — must-have de
PMS jurídico em 2026: registrar minutos trabalhados, taxa horária, vínculo
opcional a matter/client, e um resumo com estimativa de valor faturável.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `TimeEntry` em `backend/database.py` (`time_entries`) |
| Campos | id, user_id, matter_id (nullable FK), client_id (nullable FK), description, minutes (int), hourly_rate (float nullable), billable (bool default True), work_date (date), created_at |
| Rotas | `backend/routes/time_routes.py` — JWT + rate limit |
| Registro | `app.include_router(time_router)` em `main.py` |
| Schema | `Base.metadata.create_all` / `init_db` cria a tabela automaticamente |

Endpoints:

- `GET /time/entries` — lista paginada (filtros billable / matter / client / from / to)
- `POST /time/entries` — cria lançamento
- `PATCH /time/entries/{id}` — atualiza campos
- `DELETE /time/entries/{id}` — remove
- `GET /time/summary` — total minutes + `billable_amount_estimate`

### Frontend

- Página trust-shell: `frontend/app/dashboard/time/page.tsx`
- Lista + formulário (description, minutes, rate) + cards de resumo
- Usa `apiFetch('/time/entries')` e `apiFetch('/time/summary')`
- Link em Ações Rápidas do dashboard: **Time Entries**

### Testes

- `backend/tests/test_time_routes.py` — create/list, patch, summary, delete,
  IDOR 404, auth obrigatória, minutes inválidos
- App mínimo com `TestClient` (sem importar `main`); **≥5 testes**

## Decisões de desenho

1. **Model no `database.py`** — alinhado a Matter / Invoice; domínio ainda pequeno.
2. **Ownership por `user_id`** — multi-tenant simples (mesmo padrão de matters).
3. **matter_id / client_id validados** — só aceita registros do mesmo user (400).
4. **Estimativa** — `(minutes / 60) * hourly_rate` só para entradas `billable`
   com taxa definida; UI mostra no resumo e por linha.
5. **UI trust (navy/teal)** — consistente com overnight design / Matters / Intake.

## Como validar

```bash
cd backend
pytest tests/test_time_routes.py -q
```

UI: login → Dashboard → **Time Entries** → lançar horas → ver estimativa.

## Próximos passos (fora deste MVP)

- Vincular time entry a matter/client na UI (dropdown)
- Export CSV / fatura a partir dos lançamentos
- Timer start/stop e arredondamento de minutos
- Migração Alembic explícita para DBs já existentes
