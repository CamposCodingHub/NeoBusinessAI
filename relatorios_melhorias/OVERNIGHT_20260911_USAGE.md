# Overnight 2026-09-11 — Usage metering (SaaS limits)

Data: 11 de setembro de 2026

## Objetivo

Adicionar medicao pragmatica de uso (documentos + mensagens de IA/dia)
com limites por plano, checagens leves no upload autenticado e no chat
premium, e um endpoint autenticado de snapshot — sem quebrar free/dev/test.

## O que foi implementado

### 1. Servico `usage_metering`

Arquivo: `backend/services/usage_metering.py`

- `count_user_documents(db, user_id)`
- `count_user_ai_messages_today(db, user_id)` — conta `ChatMessage` com
  `role=user` (ou `sender_type=user` se role nulo) desde meia-noite UTC
- `get_plan_limits(plan_tier)` → `max_documents`, `max_ai_messages_per_day`,
  `max_users` para starter / professional / business
- `check_can_upload` / `check_can_chat` → `{allowed, reason, usage, limits}`
- Plano desconhecido / `free` / vazio → **starter**
- `ENVIRONMENT=test` → nao bloqueia (`reason=test_environment_skip`)

Limites iniciais:

| Plano         | Docs | AI msgs/dia | Users |
|---------------|------|-------------|-------|
| starter       | 10   | 100         | 1     |
| professional  | 100  | 1000        | 5     |
| business      | 1000 | 10000       | 25    |

### 2. Wiring

- `backend/routes/document_routes.py` (`POST /documents/upload`):
  chama `check_can_upload`; se bloqueado → **402** com JSON claro
  (`usage_limit_http_payload`). Fallback legado se metering falhar.
- `backend/main.py` (`POST /api/chat/premium`):
  chama `check_can_chat` apos auth; se bloqueado → **402** JSON.
  Falha de metering so gera warning (chat segue).

### 3. Endpoint de snapshot

Arquivo: `backend/routes/usage_routes.py` (registrado em `main.py`)

- `GET /usage/me` (JWT) → plan_tier, usage, limits, can_upload, can_chat

### 4. Testes

Arquivo: `backend/tests/test_usage_metering.py` (sem import de `main`)

- limites por plano + fallback starter
- contagem de documentos e mensagens do dia
- bloqueio de upload / chat no limite
- skip em `ENVIRONMENT=test`
- shape do payload HTTP

## Como validar

```powershell
cd backend
$env:ENVIRONMENT="development"
python -m pytest tests/test_usage_metering.py -q
```

## Notas pragmaticas

- Nao altera billing Stripe; e um gate leve para escalabilidade SaaS.
- Contagem de AI usa persistencia `ChatMessage` (ja usada pelo chat premium).
- Em CI/`ENVIRONMENT=test` o bloqueio estrito fica desligado de proposito.
- Proximos passos opcionais: contar `max_users` via team, cache Redis
  diario, e alinhar `documents_limit` na tabela `users` aos maps do servico.
