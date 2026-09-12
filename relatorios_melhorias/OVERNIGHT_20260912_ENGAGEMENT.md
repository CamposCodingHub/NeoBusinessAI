# Overnight 2026-09-12 — Engagement Letter (contrato de honorários)

Data: 12 de setembro de 2026

## Objetivo

Stub pragmático de **contrato de honorários** para rentabilidade do escritório:
gerar rascunho markdown a partir de cliente + modalidade de fee, **sem LLM**,
com ownership JWT.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Endpoint | `POST /legal/engagement-letter` (JWT + rate limit) em `legal_routes.py` |
| Template | `build_engagement_letter_markdown()` — Python puro |
| Persistência | **Não** grava Document; só retorna draft |

Body:

```json
{
  "client_id": 1,
  "matter_id": null,
  "fee_type": "hourly",
  "amount": null,
  "hourly_rate": 450.0,
  "scope": "Assessoria e defesa em reclamação trabalhista"
}
```

`fee_type`: `hourly` | `flat` | `contingency`

Resposta:

```json
{
  "draft_markdown": "# CONTRATO DE HONORÁRIOS...",
  "warnings": ["revisar com advogado"],
  "client_id": 1,
  "matter_id": null,
  "fee_type": "hourly"
}
```

Comportamento:

- Cliente deve pertencer ao usuário autenticado → senão **404**.
- `matter_id` opcional: ownership do matter; se `matter.client_id` existir e
  divergir do `client_id` do body → **400**.
- Nome do cliente vem do DB; nome do advogado do `User.name` (fallback email).
- Warnings extras se `hourly` sem `hourly_rate` ou `flat`/`contingency` sem `amount`.

### Testes

- `backend/tests/test_engagement_letter.py` — ≥3 casos de rota + template helper:
  - draft hourly com matter + markdown com nome do cliente
  - flat sem amount → warning
  - IDOR (cliente de outro user) → 404
  - auth obrigatória

## Decisões de desenho

1. **Só retornar draft** — evita poluir `documents` com rascunhos; UI/advogado
   decide se salva depois.
2. **Sem LLM** — template determinístico, barato e auditável para MVP de
   rentabilidade.
3. **Wire em `/legal`** — domínio jurídico já existente; reutiliza router
   registrado em `main.py`.

## Como validar

```bash
cd backend
pytest tests/test_engagement_letter.py -q
```

## Próximos passos (fora deste MVP)

- Persistir como Document / LegalDocument sob flag `save=true`
- PDF + assinatura eletrônica
- UI no dashboard (pré-preencher fee a partir de time entries)
- Cláusulas OAB / foro / rescisão configuráveis por escritório
