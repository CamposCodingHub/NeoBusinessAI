# DAY 2026-09-12 — Protocolos judiciais

## Dor
Advogado protocola no PJe/e-SAJ e perde o número no print/e-mail do tribunal.

## Entrega
| Path | Papel |
|------|--------|
| `CourtProtocol` em `database.py` | Modelo `court_protocols` |
| `GET/POST /protocols`, `PATCH /protocols/{id}/status` | JWT CRUD local |
| `/dashboard/protocolos` | UI registrar + confirmar |
| Painel Hoje + briefing | `protocols_pending` |
| `tests/test_protocols_routes.py` | ownership + CRUD |

## Status
`pending` → `confirmed` | `returned` | `archived`

Sistemas: `pje` | `esaj` | `projudi` | `tj` | `outro`

Não sincroniza com tribunal — só evita extravio do comprovante.
