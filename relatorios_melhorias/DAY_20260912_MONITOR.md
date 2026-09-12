# DAY_20260912 — DJEn / intimação monitoring stub

Data: 12 de setembro de 2026 (daytime polish, tick 6 — market gap)

## O que é

Stub de **monitoramento de processos / intimações** no estilo DJEn:

| Peça | Papel |
| --- | --- |
| `MonitoredProcess` | Cadastro local (número, tribunal, OAB, status active\|paused) |
| `IntimacaoEvent` | Evento associado; `source` default `"stub"` |
| `POST .../poll-stub` | Gera **1 evento fake** claramente rotulado e atualiza `last_checked_at` |

**Não** é scrape CNJ, **não** é API oficial DJEn / DataJud, **não** há integração com tribunal.

## Entrega

| Item | Detalhe |
| --- | --- |
| Models | `MonitoredProcess`, `IntimacaoEvent` em `backend/database.py` |
| API JWT | `backend/routes/monitor_routes.py` — prefix `/monitor` |
| UI | `/dashboard/monitor` + link **Monitor** em Operações |
| Testes | `backend/tests/test_monitor_routes.py` (≥4) |
| Eval | `python scripts/run_professional_domain_eval.py` → 14/14 |

### Endpoints

- `POST /monitor/processes` — cadastrar
- `GET /monitor/processes` — listar do usuário
- `POST /monitor/processes/{id}/poll-stub` — fake intimação + `last_checked_at`
- `GET /monitor/processes/{id}/events` — listar eventos
- `POST /monitor/events/{id}/ack` — `acknowledged=true`

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_monitor_routes.py -q
.\venv311\Scripts\python.exe scripts/run_professional_domain_eval.py
```

## Fora de escopo

Scrape DJEn/CNJ, webhooks de tribunal, OAB sync real, alertas WhatsApp/e-mail automáticos a partir de diário oficial.

Sem commit (pedido explícito).
