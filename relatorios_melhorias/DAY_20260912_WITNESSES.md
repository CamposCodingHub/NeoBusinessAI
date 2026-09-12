# DAY 2026-09-12 — Testemunhas da audiência

## Dor
Na véspera da audiência o escritório não acha telefone/confirmação das testemunhas.

## Entrega
| Path | Papel |
|------|--------|
| `HearingWitness` | Modelo `hearing_witnesses` |
| `GET/POST /agenda/hearings/{id}/witnesses` | Lista / adiciona |
| `PATCH /agenda/witnesses/{id}/status` | pending → confirmed / waived |
| Agenda UI | Botão Testemunhas + formulário rápido |
| `test_agenda_routes.py` | CRUD + IDOR |

Contato operacional local — não é intimação judicial nem sync com tribunal.
