# Day tick 10 — incidente main.py routers

## Problema
`main.py` perdeu includes de rotas overnight/day (matters, intake, orgs, trust, …) e JWT em `/api/documents` + `/chat-stream`. Security middleware estava comentado. QA caiu para **48**.

## Correção
- Re-include routers: matter, intake, approvals, time, usage, ai_audit, org, trust, esign, monitor, compliance, notification, billing
- `setup_security_middleware` reativado
- `/api/documents` e `/chat-stream` exigem JWT; chat-stream usa Lex premium quick quando disponível
- Rate limit em development: simulador atingiu 429 — ajustar/bypass localhost

## Pós-fix parcial
Módulos voltaram 200; score temporário 88 por 429 no fim da bateria.
