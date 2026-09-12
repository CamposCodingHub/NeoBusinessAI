# Overnight 2026-09-11 — Matters MVP (market gap: unified case lifecycle)

Data: 11 de setembro de 2026

## Objetivo

Fechar o gap de **ciclo de vida unificado de casos (Matter/Case)** para SaaS
jurídico: um registro operacional com status `open|pending|closed`, vínculo
opcional a cliente, e FKs nullable em Document/Deadline — MVP pragmático e
escalável, sem quebrar fluxos existentes.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `Matter` em `backend/database.py` (`matters`) |
| Campos | id, user_id, client_id (nullable FK), title, practice_area, status (`open\|pending\|closed`), opposing_party, court, process_number, notes, created_at, updated_at |
| FKs opcionais | `Document.matter_id` e `Deadline.matter_id` (nullable, indexados) |
| Rotas | `backend/routes/matter_routes.py` — JWT + rate limit |
| Registro | `app.include_router(matter_router)` em `main.py` |
| Schema | `Base.metadata.create_all` / `init_db` cria a tabela automaticamente |

Endpoints:

- `GET /matters` — lista paginada (filtros status / search / practice_area / client_id)
- `POST /matters` — cria matter
- `GET /matters/{id}` — detalhe (ownership)
- `PATCH /matters/{id}` — atualiza campos / status do ciclo de vida

### Frontend

- Página trust-shell: `frontend/app/dashboard/matters/page.tsx`
- Lista filtrável por status + formulário de criação + mudança rápida de status
- Usa `apiFetch('/matters')` (token também resolve `neobusiness_tokens`)
- Link em Ações Rápidas do dashboard: **Casos / Matters**

### Testes

- `backend/tests/test_matter_routes.py` — create/list, get by id, patch,
  status inválido, client_id próprio, IDOR 404, auth obrigatória
- App mínimo com `TestClient` (sem importar `main`); **≥5 testes**

## Decisões de desenho

1. **Model no `database.py`** — alinhado a `Lead` / `Client`; domínio ainda pequeno.
2. **Ownership por `user_id`** — multi-tenant simples (mesmo padrão de intake).
3. **`client_id` validado** — só aceita Client do mesmo user (400 se inválido).
4. **FKs nullable em Document/Deadline** — permite vincular depois; fluxos atuais
   ignoram a coluna e continuam válidos.
5. **UI trust (navy/teal)** — consistente com overnight design / Intake.

## Como validar

```bash
cd backend
pytest tests/test_matter_routes.py -q
```

UI: login → Dashboard → **Casos / Matters** → criar caso → filtrar / mudar status.

## Próximos passos (fora deste MVP)

- UI para vincular Document e Deadline a um matter
- Migração Alembic explícita para DBs já existentes (ADD COLUMN matter_id)
- Timeline de andamentos / tarefas por matter
- Deep-link matter ↔ client ↔ intake convertido
