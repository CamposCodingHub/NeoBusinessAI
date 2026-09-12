# Overnight 2026-09-12 — LGPD/GDPR export (firm user)

Data: 12 de setembro de 2026

## Objetivo

Pacote de portabilidade escalável para o usuário autenticado do escritório
(JWT), sem derrubar o export se uma tabela estiver ausente e sem vazar
`password_hash` / segredos.

## Entrega

### Service

`backend/services/compliance_service.py` → `ComplianceService.export_user_data`:

- Usa modelos de `database.py` (stack do firm), não o pacote paralelo `models/`
- Seções **best-effort** (`partial_errors` se uma query falhar)
- Profile sem `password_hash` / denylist de segredos
- Contagens: `clients_count`, `chat_messages_count`, `leads_count`, `matters_count`
- `documents`: metadados (id, filename, datas, tipo/tamanho/status) — **sem** texto completo
- `invoices_summary`: count, total_cents, by_status, items resumidos

### Endpoints

| Método | Path | Auth |
| --- | --- | --- |
| GET | `/gdpr/export` | JWT |
| POST | `/gdpr/export` | JWT |
| GET | `/gdpr/export/my-data` | JWT (alias legado) |

Rotas em `backend/routes/gdpr_routes.py` — enriquecem o export existente em vez de
criar pipeline paralelo.

### Testes

`backend/tests/test_gdpr_export.py` — 5 casos:

1. GET export: shape + contagens + sem `password_hash` + sem texto de documento
2. POST export: mesmo shape
3. Sem JWT → 401/403
4. Alias legado + best-effort (seção leads falha isolada)
5. Service `_profile_from_user` nunca inclui hash

## Como validar

```bash
cd backend
pytest tests/test_gdpr_export.py -q
```

## Fora deste MVP

- Export assíncrono / download ZIP para tenants grandes
- Inclusão opcional de conteúdo de documentos sob consentimento explícito
- Alinhamento completo do fluxo de delete com leads/matters/chat

## Frontend (settings)

`frontend/app/settings/page.tsx` — seção trust mínima **Privacidade (LGPD)** com botão
`Exportar meus dados (LGPD)`: chama `GET /gdpr/export` via `apiFetch` (mesmo auth
`hasToken` / JWT da página) e dispara download JSON via blob/`createObjectURL`.

Sem commit.
