# Overnight 2026-09-11 — Lex AI: busca interna + escopo juridico/contabil

Data: 11 de setembro de 2026

## Objetivo

Tornar a Lex capaz de (1) buscar documentos do usuario dentro do produto,
(2) responder perguntas de advocacia e de contabilidade/fiscal operacional
com tom profissional (sem coach de SaaS e sem emojis), e (3) permanecer
ancorada em evidencias recuperadas, com disclaimer forte em materia fiscal.

## O que foi implementado

### 1. Busca interna de documentos

Arquivo novo: `backend/services/internal_document_search.py`

- `search_user_documents(db, user_id, query, top_k=...)` filtra candidatos
  com SQL `ILIKE` nas colunas live do `Document` (`filename`, `summary`,
  `text_content`, `document_type`, `analysis`, cast de `parties`) e, como
  fallback legado, cast de `content` (onde o pipeline antigo guardava
  `extracted_text` / `document_type`).
- Ranking em Python nos mesmos campos (pesos: filename > tipo > partes >
  summary > analysis > text_content), alinhado a `document_to_dict`.
- Retorno (API estavel): `document_id`, `filename`, `document_type`, `score`,
  `excerpt`, `status`.
- Helpers: `build_document_context`, `looks_like_user_document_query`,
  `looks_like_accounting_tax_query`.

Correcao de mapeamento (mesma data): o rascunho inicial lia texto/tipo
apenas de `content.extracted_text` / `content.document_type`. O modelo live
e a serializacao (`document_to_dict`) usam colunas `text_content` e
`document_type`; o pipeline agora tambem as preenche, mantendo `content`
JSON apenas como compatibilidade.

### 2. Orquestrador Lex

Arquivo: `backend/services/legal_ai_orchestrator.py`

- Em intents de documento do usuario ("meu contrato", "meus documentos",
  "o que diz o PDF", etc.), busca o acervo e injeta em `document_context`.
- Intents contabeis/fiscais (ISS/ICMS/IRPJ/Simples, classificacao de
  despesas, obrigacoes acessorias) ativam dominio `contabil_fiscal`,
  regras de nao inventar aliquotas e aviso de que **nao e parecer vinculante**.
- Metadata nova: `internal_document_search_used`, `internal_document_hits`,
  `accounting_intent`.

### 3. Prompts do motor premium

Arquivo: `backend/ai/premium_conversational_engine.py`

- Lex cobre advocacia BR, contabilidade/fiscal operacional e operacao do
  escritorio no produto (prazos, clientes, documentos, financeiro).
- Removido incentivo a emojis e tom de Legal Tech/SaaS coach.
- Reforco de grounding e disclaimer fiscal.

### 4. Endpoint autenticado

Arquivo: `backend/routes/document_routes.py`

- `GET /documents/search?q=&limit=` — busca nos documentos do usuario logado
  via `search_user_documents` (mesmos campos live acima).

### 5. Chat premium

Arquivo: `backend/main.py`

- Resposta do `/api/chat/premium` expoe `internal_document_search_used`,
  `internal_document_hits` e `accounting_intent`.

### 6. Modelo Document + processamento

- Colunas live alinhadas a `document_to_dict`: `text_content`,
  `document_type`, `process_number`, `court` (alem de `filename`, `summary`,
  `parties`, `analysis`).
- `document_processing_service` grava `text_content` / `document_type` (e
  metadados) nas colunas; `content` JSON permanece como espelho legado.
- Migracao SQLite local adiciona as colunas se faltarem.

### 7. Testes

Arquivo novo: `backend/tests/test_internal_document_search.py`

- Ranking lexical com sessao mockada (coluna `text_content` e fallback
  `content.extracted_text`).
- Isolamento por user_id (docs do dono).
- Heuristicas de intent documento / fiscal.
- Injecao de contexto no orquestrador.
- Marcacao de intent contabil e disclaimer no `system_context`.

## Como validar

```bash
cd backend
python -m pytest tests/test_internal_document_search.py -q
```

Manual sugerido:

1. Autenticar e chamar `GET /documents/search?q=contrato`.
2. No chat premium: "O que diz o meu contrato sobre multa?"
3. No chat premium: "Como classificar despesa de software no Simples?" —
   esperar dominio contabil e aviso de revisao profissional / sem aliquota inventada.

## Limites conscientes

- Ranking e lexical/semantic-ish (tokens + pesos), nao embedding vectorial.
- Depende de texto ja extraido em `text_content`/`summary`/`analysis` (ou
  `content` legado); docs so uploaded sem analise tendem a ranquear pouco.
- Aliquotas municipais/estaduais continuam fora do inventário se nao vierem
  nas fontes oficiais recuperadas — comportamento intencional.

## Nao feito nesta rodada

- Commit Git (conforme pedido).
- Alteracoes em `venv` / `venv311`.
