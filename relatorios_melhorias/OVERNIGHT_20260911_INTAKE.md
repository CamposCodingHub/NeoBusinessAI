# Overnight 2026-09-11 — Intake MVP (market gap #1)

Data: 11 de setembro de 2026

## Objetivo

Fechar o gap de **intake / captação comercial** para SaaS jurídico: pipeline
de leads com status operacional, flag de conflito e conversão para o modelo
`Client` existente — MVP pragmático e escalável.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `Lead` em `backend/database.py` (`intake_leads`) |
| Campos | id, user_id, name, email, phone, practice_area, source, status (`new\|qualified\|meeting\|won\|lost`), notes, conflict_flag, conflict_detail, created_at, updated_at |
| Rotas | `backend/routes/intake_routes.py` — JWT + rate limit |
| Registro | `app.include_router(intake_router)` em `main.py` |
| Schema | `Base.metadata.create_all` / `init_db` cria a tabela automaticamente |

Endpoints:

- `GET /intake/leads` — lista paginada (filtros status / search / practice_area)
- `POST /intake/leads` — cria lead
- `PATCH /intake/leads/{id}` — atualiza campos / move no kanban
- `POST /intake/leads/{id}/convert` — cria `Client`, marca lead `won`; bloqueia se `conflict_flag`

### Frontend

- Página trust-shell: `frontend/app/dashboard/intake/page.tsx`
- Kanban por status + formulário de criação + converter
- Usa `apiFetch('/intake/leads')` (token também resolve `neobusiness_tokens`)
- Link em Ações Rápidas do dashboard: **Intake / Leads**

### Testes

- `backend/tests/test_intake_routes.py` — create/list, patch, status inválido,
  convert → Client, conflito 409, IDOR 404, auth obrigatória
- App mínimo com `TestClient` (sem importar `main`) para evitar deps opcionais
  ausentes no ambiente local; **7/7 passed**

## Decisões de desenho

1. **Model no `database.py`** — alinhado a `Client` / `Invoice`; evita módulo
   órfão enquanto o domínio ainda é pequeno.
2. **Ownership por `user_id`** — multi-tenant simples (mesmo padrão de clients).
3. **Convert reutiliza `Client`** — sem segundo CRM; notas recebem metadados
   de área/fonte do intake.
4. **Conflict flag** — gate explícito na conversão (409), sem workflow pesado.
5. **UI trust (navy/teal)** — consistente com overnight design; não reescreve
   o dashboard legado.

## Como validar

```bash
cd backend
pytest tests/test_intake_routes.py -q
```

UI: login → Dashboard → **Intake / Leads** → criar lead → mover status → converter.

## Conflict screening (follow-up)

Ver `OVERNIGHT_20260911_CONFLICT.md`: screening automático em create/patch
contra Clients / Matters / outros Leads; `conflict_detail` + prefixo
`[CONFLICT]` em notes; convert continua bloqueado se `conflict_flag`.

## Próximos passos (fora deste MVP)

- Public intake form (landing / WhatsApp) → `source` automático
- Checklist formal de conflito / aprovação de sócio
- `converted_client_id` no lead + deep-link para ficha do cliente
- Webhooks / CRM sync (HubSpot, etc.) se necessário
