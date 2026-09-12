# Overnight 2026-09-12 — Lex chat metadata strip

Data: 12 de setembro de 2026

## Objetivo

Expor, de forma mínima e legível, metadados úteis da Lex nas respostas do
chat principal (`frontend/app/chat/page.tsx`), quando presentes no `metadata`
da API (`/api/chat/premium`), sem reescrever a página.

## O que foi feito

### `AiMetadata` (já anexado em `Message.metadata`)

Campos novos tipados (já enviados pelo backend em `main.py`):

| Campo | Uso na UI |
| --- | --- |
| `internal_document_search_used` | Mostra “Docs internos” + contagem de hits |
| `internal_document_hits` | Array; UI usa `.length` |
| `professional_domain` | Preferido sobre `legal_area` como “Dominio” |

Campos já existentes e agora renderizados no bubble:

- `legal_area` (fallback se não houver `professional_domain`)
- `grounding_status`
- `requires_human_review` (só quando `true` → “Revisao humana”)
- `response_mode`

### UI

- Componente `LexMetaStrip` sob o markdown do assistente: texto `slate` /
  valores `teal`, sem cards nem emoji.
- Strip só aparece se houver pelo menos um item presente.
- Header do chat: link **Auditoria IA** → `/dashboard/ai-audit`.

### Fora de escopo

- `frontend/components/premium-chat.tsx` — sem imports no app; não alterado.
- Sem commit.

## Como validar

1. Login → `/chat` → pergunta premium.
2. Após resposta, conferir faixa sob o texto (docs / domínio / grounding /
   revisão / modo) quando o backend incluir esses campos.
3. Header: link **Auditoria IA** abre `/dashboard/ai-audit`.
