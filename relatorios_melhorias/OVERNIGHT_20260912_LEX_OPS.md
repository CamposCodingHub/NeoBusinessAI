# Overnight 2026-09-12 — Lex operacional (atalhos + prompts)

Data: 12 de setembro de 2026

## Objetivo

Melhorar a utilidade operacional da Lex de forma cirurgica: deixar claro o que o
usuario pode perguntar no produto, expor atalhos dos modulos do dashboard e
sugerir prompts uteis no chat — sem pitch de SaaS e sem commit.

## O que foi feito

### 1. Addenda / escopo de produto

- `backend/ai/professional_domains.py` — addendum `escritorio_ops`: se perguntarem
  o que da para consultar/fazer, citar de forma objetiva: prazos, matters,
  intake/COI, time entries, aprovacoes WhatsApp, limites de uso e busca em
  documentos.
- `backend/services/legal_ai_orchestrator.py` — bloco `ESCOPO PROFISSIONAL DA LEX`
  alinhado (explicar o que pedir / onde olhar, sem pitch).

### 2. `GET /operations/shortcuts` (JWT)

Arquivo: `backend/routes/operations_routes.py`

Retorna `{ shortcuts: [{ label, path, description }, ...] }` para:

| Label | Path |
| --- | --- |
| Prazos | `/dashboard/deadlines` |
| Matters | `/dashboard/matters` |
| Intake / COI | `/dashboard/intake` |
| Time entries | `/dashboard/time` |
| Aprovacoes WhatsApp | `/dashboard/approvals` |
| Documentos | `/dashboard/documents` |
| Limites de uso | `/pricing` (detalhe atual tambem em `GET /usage/me`) |

`/usage/me` continua sendo a fonte de metering; o endpoint de shortcuts e para
navegacao de modulos, nao substitui o usage.

### 3. Chat — prompt chips (trust teal)

Arquivo: `frontend/app/chat/page.tsx`

Quatro chips clicaveis (preenchem o input):

1. Busque nos meus documentos sobre contrato
2. Riscos do meu prazo
3. Como classificar ISS no Simples sem inventar aliquota?
4. Resumo operacional do escritorio

Estilo: borda/fundo teal (trust), tambem na coluna lateral "Sugestoes".

### Fora de escopo

- Sem commit.
- Sem alterar `frontend/src/app/chat/page.tsx` (rota legado / paralelo).

## Como validar

1. Login JWT → `GET /operations/shortcuts` → lista com label/path/description.
2. `/chat` → clicar chip → input preenchido com o texto do prompt.
3. Perguntar "o que posso ver no produto?" com dominio ops → resposta objetiva
   citando prazos/matters/intake/time/aprovacoes/limites/documentos, sem pitch.
