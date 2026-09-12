# DAY_20260912 — Trust three-way reconciliation stub

Data: 12 de setembro de 2026 (daytime polish, tick 2)

## O que é

Stub de **reconciliação tripartite** no ledger trust (IOLTA-style):

| Lado | Origem |
| --- | --- |
| `book_balance` | Saldo do livro (`deposits − withdrawals − transfers + adjustments`) |
| `client_subtotals` | Mesma fórmula agrupada por `client_id` (não nulo) |
| `unallocated_balance` | Mesma fórmula onde `client_id IS NULL` |

**Não** é feed bancário / Open Finance / PIX. Campo `note`: `"stub — not bank feed"`.

## Entrega

| Item | Detalhe |
| --- | --- |
| API | `GET /trust/accounts/{id}/reconcile` em `backend/routes/trust_routes.py` |
| UI | Botão **Resumo reconciliação** + painel em `frontend/app/dashboard/trust/page.tsx` |
| Testes | `backend/tests/test_trust_reconcile.py` (split client/unallocated + IDOR/auth/empty) |

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_trust_reconcile.py -q
```

## Fora de escopo

Conciliação com extrato bancário, interest accounting IOLTA, bloqueio de saldo negativo.

Sem commit (pedido explícito).
