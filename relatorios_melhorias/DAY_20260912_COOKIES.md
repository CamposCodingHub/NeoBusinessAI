# DAY_20260912 — Auth cookies HttpOnly (MVP)

## Objetivo
Endurecer autenticação para cookies de produção **sem** quebrar o fluxo JWT Bearer + `localStorage` usado pelo frontend hoje.

## O que foi feito
1. **Cookie `access_token`** em login / register / refresh (`httponly=True`, `samesite=lax`, `path=/`, `secure=True` só se `ENVIRONMENT` ∈ `{staging, production}`).
2. Body JSON continua com `access_token` + `refresh_token` (`token_type: bearer`) — compatível com o front atual.
3. **`get_current_user`** aceita `Authorization: Bearer …` **ou** cookie `access_token` (Bearer tem prioridade).
4. **`POST /auth/logout`** limpa o cookie e blacklista o token (Bearer ou cookie).
5. Frontend (`lib/api.ts`): `credentials: 'include'` em `apiFetch` / login / logout / refresh; comentário documentando dual-mode. **Nenhuma página foi migrada** — Bearer + localStorage segue o caminho padrão.

## Testes
- `tests/test_auth_cookies.py` (app mínimo com `auth_router`): cookie set no login/register; `/auth/me` autenticado só via cookie; logout blacklista token.
- `tests/test_auth.py`: assertion extra de cookie no `test_login_success` (requer `main` importável).

## Nota operacional — `venv311` no git
O diretório `backend/venv311` **não deve** estar versionado. Se ainda aparecer no índice:

```bash
git rm --cached -r backend/venv311
```

(isso só remove do índice git; **não** apaga o venv local). Confirme que `venv311/` (ou `venv/`) está no `.gitignore` e faça um commit dedicado depois. **Não rode** `git rm` destrutivo sem revisão.

## Próximos passos (fora deste MVP)
- Migrar páginas do front para confiar só no cookie (remover token sensível do `localStorage`).
- CSRF se cookies forem o único canal em produção cross-site.
- Opcional: cookie separado para refresh com path restrito.
