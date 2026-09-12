# Overnight 2026-09-11 — Memoria duravel do chat premium Lex

Data: 11 de setembro de 2026

## Objetivo

Persistir o historico do chat premium alem da memoria em processo
(`AdvancedMemorySystem` keyed por `{user_id}:{conversation_id}`), hidratar
ao reiniciar o processo quando a memoria estiver vazia, e permitir limpar
uma conversa com autenticacao — sem quebrar o fluxo se o banco falhar.

## O que foi implementado

### 1. Modelo `ChatMessage`

Arquivo: `backend/database.py`

- Coluna nova `conversation_id` (nullable, indexada).
- `context_type` passa a ser indexado (filtro `premium_chat`).
- `to_dict()` expoe `conversation_id`.
- Migracao local SQLite em `_apply_sqlite_development_migrations` adiciona
  `chat_messages.conversation_id` se a tabela ja existir sem a coluna.

### 2. Servico de persistencia

Arquivo novo: `backend/services/chat_memory_service.py`

- `sanitize_conversation_id` / `parse_memory_key`
- `load_conversation_messages(db, user_id, conversation_id, limit=N)`
- `persist_turn(...)` — grava par user/assistant com
  `context_type=premium_chat`
- `clear_conversation_messages(...)`
- Toda operacao e best-effort: excecao → log + retorno vazio/`False`/`-1`
  e `rollback`, para o chat continuar memory-only.

### 3. Motor premium

Arquivo: `backend/ai/premium_conversational_engine.py`

- `ConversationMemory.hydrate_from_persisted`
- `AdvancedMemorySystem.get_or_create_memory(..., db=, hydrate=)` hidrata
  do DB quando a deque em processo esta vazia
- `AdvancedMemorySystem.clear_memory`
- `generate_premium_response` aceita `db=` opcional e hidrata via
  `get_or_create_memory` (abre `SessionLocal` se `db` nao for passado)

### 4. Endpoint premium

Arquivo: `backend/main.py`

- Apos sucesso de `/api/chat/premium`, chama `persist_turn` (falha so
  gera warning; resposta ao cliente permanece 200).
- `DELETE /api/chat/premium/memory?conversation_id=` e
  `POST /api/chat/premium/memory/clear` (body JSON) — autenticados —
  apagam DB + memoria em processo.
- Feature flag em `/api/ai/status`: `memoria_duravel`.

### 5. Testes

Arquivo: `backend/tests/test_chat_memory_persistence.py` (SQLite in-memory)

- Persist / load / clear / isolamento por conversation_id
- Hidratacao quando memoria vazia; nao rehidrata se ja houver mensagens
- Fallback quando a sessao DB esta fechada
- `generate_premium_response` hidrata historico antes da nova resposta

## Como validar

```bash
cd backend
python -m pytest tests/test_chat_memory_persistence.py -q
```

Fluxo manual:

1. `POST /api/chat/premium` com `conversation_id` fixo (duas mensagens).
2. Reiniciar o processo da API.
3. Novo `POST` na mesma conversa — o motor deve ver o historico hidratado.
4. `DELETE /api/chat/premium/memory?conversation_id=...` — limpa DB e RAM.

## Compatibilidade

- Sem DB / coluna ausente / commit falho → chat segue so com memoria em
  processo (comportamento anterior).
- WhatsApp e outros usos de `ChatMessage` nao sao afetados (filtro por
  `context_type=premium_chat` + `conversation_id`).

## Fora de escopo / nao feito

- Commit git (pedido explicito para nao commitar).
- Alteracoes em `venv` / pacotes instalados.
- Migracao Alembic alem do stub (schema novo entra via `create_all` +
  migrate SQLite local; Postgres novo tambem via `create_all`).
