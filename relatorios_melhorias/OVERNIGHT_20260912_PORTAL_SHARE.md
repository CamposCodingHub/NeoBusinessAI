# Overnight 2026-09-12 — Portal share (documento → cliente)

Data: 12 de setembro de 2026

## Objetivo

Fechar o gap transacional do portal: o escritório precisa **compartilhar um
documento** com um cliente do portal sem coluna nova — reutilizando o filtro
já existente em `GET /portal/documents` (`Matter.client_id` **ou**
`Document.custom_data.client_id`).

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Endpoint | `POST /documents/{id}/share-portal` (JWT do escritório) |
| Body | `{ "client_id": int, "matter_id"?: int }` |
| Efeito | `custom_data.client_id` (e `matter_id` se informado); opcionalmente `Document.matter_id` |
| Ownership | Documento, cliente e matter filtrados por `user_id` do token |

Resposta típica:

```json
{
  "success": true,
  "message": "Documento compartilhado com o portal do cliente",
  "document_id": 1,
  "client_id": 2,
  "matter_id": 3,
  "custom_data": { "client_id": 2, "matter_id": 3 }
}
```

**IDOR**

- Documento de outro usuário → **404**
- `client_id` / `matter_id` de outro tenant → **400**
- Matter com `client_id` diferente do body → **400**
- Sem JWT → **401**

Portal: nenhuma alteração necessária — `_documents_for_client` já une docs por
matter e por `custom_data.client_id`.

### Frontend (opcional mínimo)

- `frontend/app/dashboard/documents/page.tsx`: botão **Portal** por documento
  (prompt do `client_id` → `POST .../share-portal`).

### Testes

- `backend/tests/test_document_portal_share.py` — **6** casos:
  1. share grava `custom_data.client_id` (preserva keys anteriores)
  2. share com `matter_id`
  3. IDOR documento alheio
  4. IDOR cliente alheio
  5. auth obrigatória
  6. após share, `GET /portal/documents` lista o doc

## Como validar

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_document_portal_share.py -q
```

Fluxo manual: Dashboard → Documentos → **Portal** → informar `client_id` →
login em `/portal` com o `PortalClient` desse cliente → aba Documentos.

## Decisões

1. **Tag em `custom_data`** — zero migração; alinhado ao portal overnight 11/09.
2. **`matter_id` opcional** — permite também o caminho Matter→client_id.
3. **UI prompt** — suficiente para fechar o gap; seletor de clientes fica para
   polish posterior.
