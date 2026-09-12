# DAY_20260912 — Agenda / audiências stub

Data: 12 de setembro de 2026 (daytime polish — lawyer daily pain)

## O que é

Stub de **agenda de audiências e compromissos** (dor diária do advogado: não perder audiência / compromisso):

| Peça | Papel |
| --- | --- |
| `Hearing` | Compromisso local (`hearing_at`, local, status scheduled\|done\|cancelled) |
| `GET/POST /agenda/hearings` | Listar (filtro `from`/`to`) e criar |
| `PATCH /agenda/hearings/{id}` | Atualizar só o status |

**Não** é sync Google/Outlook, **não** é feed de tribunal, **não** há push/WhatsApp automático.

## Entrega

| Item | Detalhe |
| --- | --- |
| Model | `Hearing` em `backend/database.py` |
| API JWT | `backend/routes/agenda_routes.py` — prefix `/agenda` |
| UI | `/dashboard/agenda` + link **Agenda** em Operações → Casos |
| Testes | `backend/tests/test_agenda_routes.py` (≥4) |
| Router | `agenda_router` **appended** em `main.py` (sem remover routers existentes) |

### Endpoints

- `GET /agenda/hearings?from=&to=` — listar do usuário
- `POST /agenda/hearings` — criar
- `PATCH /agenda/hearings/{id}` — `{ "status": "scheduled"|"done"|"cancelled" }`

```bash
cd backend
.\venv311\Scripts\python.exe -m pytest tests/test_agenda_routes.py -q
```

## Fora de escopo

Calendário externo, intimação automática, sala virtual, lembretes push.

Sem commit (pedido explícito).
