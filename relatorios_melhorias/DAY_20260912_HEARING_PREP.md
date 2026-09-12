# Checklist de preparação de audiência
## 12/09/2026 — tick diurno (~18:05)

### Dor
Chegar na audiência sem procuração/RG/peças/testemunhas confirmadas.

### Entrega
- Modelo `HearingPrepItem`
- API: `GET/POST .../hearings/{id}/prep`, `POST .../prep/seed`, `PATCH /agenda/prep/{id}/status`
- Seed estático: procuração, RG, peças, testemunhas, chegar cedo
- UI Agenda → botão Prep
- Testes em `test_agenda_routes.py`

### Limite
Não é pauta do tribunal nem integração PJe.
