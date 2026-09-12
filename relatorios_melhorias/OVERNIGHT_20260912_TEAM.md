# Overnight 2026-09-12 — Team invite stub (multi-user firm)

Data: 12 de setembro de 2026

## Objetivo

Stub pragmático de **convites de equipe** para escalabilidade multi-usuário do
escritório: criar, listar, revogar (JWT do owner) e aceitar via token — com
shell UI trust em `/dashboard/team`.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `TeamInvite` em `backend/database.py` |
| Schema | `id`, `owner_user_id`, `email`, `role` (`user`\|`admin`), `status` (`pending`\|`accepted`\|`revoked`), `token`, `created_at`, `accepted_at` nullable |
| Persistência | Tabela nova `team_invites` via `Base.metadata.create_all` |
| Routes | Extensão de `backend/routes/team_routes.py` (já registrado em `main.py`) |

Endpoints:

- `POST /team/invites` — JWT owner; cria pending + devolve `token` uma vez
- `GET /team/invites` — JWT owner; lista só do `owner_user_id` (sem token)
- `POST /team/invites/{id}/revoke` — JWT owner; 404 se IDOR
- `POST /team/invites/accept` — body `{token}`; sem JWT; cria stub User ou vincula existente + `note`

### Frontend (UI)

| Item | Detalhe |
| --- | --- |
| Página | `frontend/app/dashboard/team/page.tsx` — trust-shell fino |
| Listar | `GET /team/invites` via `apiFetch` |
| Convidar | formulário e-mail + role (`user`\|`admin`) → `POST /team/invites` |
| Revogar | botão → `POST /team/invites/{id}/revoke` (só pending) |
| Auth | `hasDashboardToken` + redirect `/login` (mesmo padrão matters/intake) |
| Nav | link **Equipe** na row Operações do dashboard |

Token de aceite é exibido uma vez após criar (API devolve `token` só no create).

### Testes

- `backend/tests/test_team_invites.py` — 6 casos:
  - create + list (token só no create)
  - IDOR list/revoke → 404 / lista vazia para outro user
  - accept cria stub User
  - accept vincula User existente + note
  - auth obrigatória nas rotas de owner
  - owner revoga pending

## Segurança (IDOR)

1. Create/list/revoke filtram por `owner_user_id == current_user.id`
2. Revoke de outro owner → **404** (não 403)
3. Accept só por `token` opaco (não por id numérico público)
4. Listagem não expõe `token`

## Decisões de desenho

1. **Estender `team_routes.py`** em vez de novo router — prefix `/team` já existia.
2. **Stub User no accept** — `company=team:{owner_id}`; se e-mail já existe, só marca accepted + note.
3. **Sem e-mail real** — token devolvido na API; envio fica para o próximo passo.
4. **UI thin** — list/create/revoke no trust-shell; accept continua só via API token.

## Como validar

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_team_invites.py -q
```

UI: abrir `/dashboard/team` logado → listar, convidar, revogar pending.

## Próximos passos (fora deste MVP)

- Copiar link de aceite (URL com token) na UI
- Envio de e-mail com token
- Membership real (`firm_id` / tenant) em vez de `company` stub
- Expiração de convite e rate limit por e-mail
