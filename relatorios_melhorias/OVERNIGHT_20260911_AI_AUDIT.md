# Overnight 2026-09-11 — AI Audit Trail (Lex compliance)

Data: 11 de setembro de 2026

## Objetivo

Adicionar uma **trilha de auditoria pragmática** para respostas do chat Lex
(`/api/chat/premium`), alinhada a expectativas de accountability de legal AI
em 2026: preview da pergunta/resposta, modelo/provedor, área, grounding e
flag de revisão humana — sem quebrar o caminho do chat se a gravação falhar.

## Decisão de modelo

`AIInferenceEvent` já existe (`ai_inference_events`) para auditoria **técnica
e financeira** de inferência (tokens, latency, request_id, fallback). Não
cobre previews de mensagem, `legal_area`, `grounding_status` nem
`requires_human_review`.

Por isso foi criado **`AIAuditEvent`** (`ai_audit_events`) — compliance Lex —
em paralelo, sem misturar com a telemetria soberana.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `AIAuditEvent` em `backend/database.py` |
| Campos | id, user_id, conversation_id, message_preview (200), response_preview (300), model, provider, legal_area, grounding_status, requires_human_review, created_at |
| Service | `backend/services/ai_audit_service.py` — `persist_lex_audit` best-effort |
| Hook | Após sucesso de `/api/chat/premium` em `main.py` (try/except; chat segue) |
| Rota | `GET /ai/audit` — JWT, últimos 50 do usuário atual |
| Registro | `app.include_router(ai_audit_router)` |

### Frontend

- Página trust-shell: `frontend/app/dashboard/ai-audit/page.tsx`
- Tabela: quando, mensagem, resposta, modelo/provider, área, grounding, revisão
- Links: Operações (**Auditoria IA**) + Ações Rápidas (**Auditoria IA Lex**)

### Testes

- `backend/tests/test_ai_audit.py` — auth, persist+list (truncamento), IDOR,
  limit ≤ 50 / 422, best-effort sem raise

## Como validar

```bash
cd backend
pytest tests/test_ai_audit.py -q
```

UI: login → Dashboard → **Auditoria IA** → após usar o chat premium, eventos
aparecem na tabela.

## Resiliência

1. `persist_lex_audit` captura qualquer exceção, faz `rollback` e retorna `None`.
2. O endpoint premium envolve a chamada em try/except adicional e só loga warning.
3. Falha de audit **nunca** altera status/body da resposta do chat.

## Próximos passos (fora deste MVP)

- Export CSV / retenção por plano
- Filtro por `requires_human_review` e `grounding_status`
- Ligação com fila de aprovações quando review=true
- Hash/assinatura do evento para integridade forense
