# Overnight 2026-09-11 — Portal do Cliente (market gap #2)

Data: 11 de setembro de 2026

## Objetivo

Fechar o gap de **portal do cliente transacional** (read-only MVP): login
próprio, listagem de documentos e faturas do próprio cliente, timeline
placeholder — sem misturar com JWT do escritório.

## Entrega

### Backend (`backend/routes/portal_client_routes.py`)

| Item | Detalhe |
| --- | --- |
| Auth | `POST /portal/login` com JSON (`email`/`password`) |
| Escopo | JWT com `permissions: ["portal"]` — token de staff sem claim é rejeitado |
| Me | `GET /portal/me` |
| Dashboard | `GET /portal/dashboard` — resumo + recentes |
| Docs | `GET /portal/documents`, `GET /portal/documents/{id}` |
| Faturas | `GET /portal/invoices`, `GET /portal/invoices/{id}`, download stub |
| Timeline | `GET /portal/timeline` — atividades + eventos docs/faturas |
| Chat | `GET /portal/chat` — stub vazio |

**Ownership**

- Faturas: filtro obrigatório `Invoice.client_id == portal.client_id`
- Documentos: via `Matter.client_id` **ou** `custom_data.client_id` (filtro
  portável SQLite/Postgres; exclui `status=error`)
- Detalhe de recurso alheio → **404** (anti-IDOR)

Modelos reutilizados: `PortalClient`, `Client`, `Invoice`, `Document`, `Matter`.

### Frontend

- Página trust-shell: `frontend/app/portal/page.tsx`
- Login form + após login: abas **Documentos / Faturas / Timeline**
- Token isolado em `localStorage.portal_access_token` (não sobrescreve
  token do dashboard do escritório)
- URL: `/portal`

### Testes

- `backend/tests/test_portal_client_routes.py`
- App mínimo + `TestClient` (padrão intake)
- **9/9 passed**

Cobertura: login ok/fail, auth obrigatória, claim portal, lista docs/faturas
só do dono, IDOR fatura/documento, `/me` + timeline.

## Decisões de desenho

1. **Claim `portal` no JWT** — evita colisão de `sub` entre `User.id` e
   `PortalClient.id` (staff token não entra no portal).
2. **Docs via Matter + custom_data** — pragmático; não exige coluna nova em
   `documents`.
3. **Token separado no browser** — portal e escritório podem coexistir.
4. **Timeline placeholder** — fecha o gap visual MyCase-like sem canal de
   chat real ainda.
5. **UI trust navy/teal** — alinhada ao overnight design.

## Como validar

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_portal_client_routes.py -q
```

UI: http://localhost:3000/portal → login com credencial `PortalClient` →
ver docs/faturas.

Seed manual (exemplo):

```python
# no shell do backend, com DB ativo
from models.portal_client import PortalClient
from security import get_password_hash
# criar PortalClient ligado a um Client existente
```

## Próximos passos (fora deste MVP)

- Provisionamento de acesso pelo escritório (UI admin → criar portal user)
- Download PDF real de fatura / documento
- Magic link / reset de senha
- Chat escritório ↔ cliente
- Assinatura / aceite de entregas
- Filtrar prazos estritamente por matter do cliente (hoje dashboard ainda
  pode incluir prazos sem matter)

## Relação com gaps de mercado

Fecha parcialmente o item 2 de `GAPS_MERCADO_ATUAIS_20260618.md`
(“Portal do cliente realmente transacional”) — base read-only + trust shell;
pagamentos nativos e assinatura ficam para ticks seguintes.
