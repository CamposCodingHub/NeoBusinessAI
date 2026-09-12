# Overnight 2026-09-12 — Firm activity feed

Data: 12 de setembro de 2026

## Objetivo

Feed operacional mínimo para observabilidade do escritório: registrar ações-chave
sem nunca quebrar o fluxo principal.

## Entrega

### Model

`ActivityLog` (auditoria GDPR) **não** foi reutilizado: schema diferente
(`resource_type` / `details` JSON vs feed simples).

Novo modelo `ActivityEvent` em `backend/database.py`:

| Campo | Tipo |
| --- | --- |
| id | PK |
| user_id | FK users |
| action | str |
| entity_type | str nullable |
| entity_id | int nullable |
| summary | str |
| created_at | datetime |

Tabela criada via `Base.metadata.create_all` (SQLite local).

### Helper

`backend/services/activity_feed_service.py` → `log_activity(db, user_id, action, summary, entity_type=None, entity_id=None)`:

- best-effort: `try/except` + `rollback` interno
- rotas também envolvem a chamada em `try/except`

### Instrumentação (leve)

| Ação | `action` |
| --- | --- |
| Intake lead create | `intake.lead_create` |
| Matter create | `matter.create` |
| Time → invoice | `time.invoice` |
| Payment link | `finance.payment_link` |
| Team invite | `team.invite` |

### Endpoint

`GET /operations/activity` (JWT) — últimos 50 eventos do usuário autenticado.

### Testes

`backend/tests/test_activity_feed.py` — persistência, listagem JWT, IDOR/auth,
best-effort sem raise.

## Como validar

```bash
cd backend
pytest tests/test_activity_feed.py -q
```

## Fora deste MVP

- Paginação / filtros por action
- Retenção / purge GDPR alinhado a ActivityLog

---

## Nota — UI Lex (append)

Trust-shell fino em `frontend/app/dashboard/activity/page.tsx`:

- `GET /operations/activity` via `apiFetch`
- Lista: quando, ação, resumo
- Redirect auth como demais páginas do dashboard
- Link **Atividade** → `/dashboard/activity` na row Operações do dashboard

Sem commit.
