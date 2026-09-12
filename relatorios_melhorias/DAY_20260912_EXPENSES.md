# Despesas reembolsáveis
## 12/09/2026 — tick diurno (~15:35)

### Dor
Deslocamento, correio e cópias misturam com custas judiciais ou ficam só no Excel.

### Entrega
- Modelo `ExpenseClaim` (travel / courier / copies / other)
- API JWT: `GET/POST /finance/expenses`, `PATCH /finance/expenses/{id}/status`
- Status: pending | reimbursed | denied | written_off
- Testes + check no QA simulator
- Distinto de `CostAdvance` (custas processuais)

### Limite
Sem OCR de recibo e sem integração bancária.
