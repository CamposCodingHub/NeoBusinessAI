# Overnight 2026-09-11 — Conflict-of-interest screening (Intake)

Data: 11 de setembro de 2026

## Objetivo

Adicionar **screening automático de conflito de interesse** no Intake —
must-have de PMS jurídico 2026: ao criar/atualizar lead, cruzar nome /
e-mail / telefone com Clients, Matters e outros Leads do mesmo escritório
(`user_id`).

## Entrega

| Item | Detalhe |
| --- | --- |
| Service | `backend/services/conflict_check_service.py` |
| Model | `Lead.conflict_detail` (Text) + `conflict_flag` existente |
| Rotas | `POST /intake/leads` e `PATCH /intake/leads/{id}` chamam o screen |
| Convert | Continua bloqueado com **409** se `conflict_flag=True` |
| Testes | `backend/tests/test_conflict_check.py` |

### Matching (pragmático)

- **Nome**: normalizado (lower, sem acento, espaços colapsados) + fuzzy
  (`SequenceMatcher` ≥ 0.88) ou contenção se o menor tiver ≥ 6 chars
- **E-mail**: exact case-insensitive
- **Telefone**: só dígitos; igualdade ou últimos 8–9 dígitos (BR)
- **Escopo**: `Client` (name/email/phone descriptografado), `Matter`
  (`opposing_party` / `title`), outros `Lead` (exclui o próprio no PATCH)
- **Efeito**: `conflict_flag=True`, `conflict_detail` com resumo,
  prefixo `[CONFLICT]` nas `notes`

### Convert

Sem mudança de contrato: `POST .../convert` rejeita conflito com 409.
O flag pode ser manual (`conflict_flag: true` no payload) ou automático.

## Como validar

```bash
cd backend
pytest tests/test_conflict_check.py tests/test_intake_routes.py -q
```

## Fora deste slice

- Checklist formal de COI / aprovação de sócio
- Índice full-text / vector search em base grande
- Match por CPF/CNPJ
