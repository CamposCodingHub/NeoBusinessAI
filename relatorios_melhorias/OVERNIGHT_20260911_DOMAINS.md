# Overnight 2026-09-11 — Lex professional domains (advogado + contador)

Data: 11 de setembro de 2026

## Objetivo

Ampliar cobertura da Lex para casos de uso de advocacia e contabilidade/fiscal
operacional, com addenda de system prompt por dominio e regras fiscais seguras
(nao inventar aliquotas; citar incerteza; disclaimer de nao parecer vinculante).

## O que foi feito

### 1. Modulo de dominios

Arquivo novo: `backend/ai/professional_domains.py`

- Detectores para: `trabalhista`, `civel`, `tributario`, `contabil_fiscal`,
  `societario`, `escritorio_ops`
- Addenda curadas por dominio + bloco `SAFE_FISCAL_RULES`
- Matching com fronteira de palavra para marcadores ambíguos (`quota`/`aliquota`,
  `cisao`/`rescisao`, `iss`, etc.)
- Helpers: `detect_professional_domains`, `build_domain_system_addenda`,
  `enrich_detected_area`, `looks_like_accounting_tax_query`

### 2. Orquestrador

Arquivo: `backend/services/legal_ai_orchestrator.py`

- Detecta dominios na mensagem e injeta addenda no `system_context`
- Enriquece `legal_area` quando estava `geral`
- Metadata: `detected_domains`, `domain_addenda_applied`, `office_ops_intent`
- `looks_like_accounting_tax_query` passa a vir do modulo de dominios
  (via import direto no orquestrador; `internal_document_search` reexporta)

### 3. Eval offline

- Dataset: `backend/evals/professional_domains_v1.json` (14 casos)
- Script: `backend/scripts/run_professional_domain_eval.py`
- Valida detectores + presença de keywords/disclaimer **sem chamar LLM**

Resultado local: **14/14** (`pass_rate=1.0`).

## Como rodar

```bash
cd backend
python scripts/run_professional_domain_eval.py
```

## Fora de escopo / proximo passo

- Nao houve commit.
- Nao houve alteracao de `venv`.
- Proximo: testes unitarios do orquestrador cobrindo `detected_domains` e
  addenda injetada no `system_context` com monkeypatch (sem LLM).
