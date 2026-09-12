# DAY_20260912 — Business-day deadline helper

Data: 12 de setembro de 2026 (daytime polish, tick 8)

## O que e

Helper de **dias uteis** para prazos processuais (calendario BR simplificado):

| Peca | Papel |
| --- | --- |
| `services/business_days.py` | `is_weekend`, `add_business_days`, feriados nacionais FIXOS |
| `POST /deadlines/compute-business` | JWT: `{ start_date, business_days }` -> `{ due_date, calendar_days_span, note }` |
| UI opcional | Preview na pagina `/dashboard/deadlines` |

**Incompleto por desenho:** so datas fixas (01-01, 21-04, 01-05, 07-09, 12-10, 02-11, 15-11, 25-12) no ano corrente/seguinte. Sem Carnaval, Sexta Santa, Corpus Christi, feriados locais ou suspensoes judiciais.

## Entrega

| Item | Detalhe |
| --- | --- |
| Service | `backend/services/business_days.py` |
| API | Wired em `backend/routes/deadline_routes.py` (router ja em `main.py`) |
| Testes | `backend/tests/test_business_days.py` (>=5) |
| Lex seed | +~10 exemplos em `seed_professional_lex_examples.py` |
| Eval | `python scripts/run_professional_domain_eval.py` -> 14/14 |

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_business_days.py -q
.\venv311\Scripts\python.exe scripts/run_professional_domain_eval.py
.\venv311\Scripts\python.exe scripts/seed_professional_lex_examples.py --dry-run
```

## Fora de escopo

Feriados moveis, calendarios de tribunal, contagem CPC automatica por tipo de ato.

Sem commit (pedido explicito).
