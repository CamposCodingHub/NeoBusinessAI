# Overnight 2026-09-12 — Deadline alert preferences

Data: 12 de setembro de 2026

## Objetivo

Preferências pragmáticas de alerta de prazos para o firm user: canais, antecedência
e quiet hours — sem envio real de e-mail neste MVP; só preview do digest.

## Entrega

### Backend

| Item | Detalhe |
| --- | --- |
| Model | `NotificationPreference` em `backend/database.py` (tabela dedicada) |
| Schema | `user_id` unique, `email_enabled` (default True), `whatsapp_enabled` (default False), `days_before` (default 3), `quiet_hours_start/end` (nullable 0–23) |
| Persistência | `Base.metadata.create_all` cria a tabela SQLite (sem ALTER em tabela existente) |
| Service | `backend/services/notification_preference_service.py` — get/create, update, `list_deadlines_needing_alert` |
| Routes | `backend/routes/notification_routes.py` registrado em `main.py` |

Endpoints (JWT):

- `GET /notifications/preferences` — get-or-create defaults
- `PUT /notifications/preferences` — atualiza campos; `clear_quiet_hours` limpa quiet hours
- `GET /notifications/deadline-digest` — preview: prefs + prazos pendentes na janela `days_before` (não envia nada)

Helper `list_deadlines_needing_alert(db, user_id, days_before=None)`:

- `is_completed == False`
- `due_date` não nulo e `<= now + days_before` (inclui atrasados)
- Ownership por `user_id`

### Frontend

- `frontend/app/settings/page.tsx` — UI mínima de alertas (e-mail, WhatsApp, dias, quiet hours) + contagem do digest preview via `apiFetch`.
- Nota: existe também `frontend/src/app/settings/page.tsx` (UI legada mock); a rota ativa do App Router em `app/` foi a usada.

### Testes

- `backend/tests/test_notification_preferences.py` — 6 casos:
  - GET cria defaults
  - PUT atualiza e persiste
  - PUT rejeita `days_before` inválido (422)
  - digest preview filtra janela + completed + IDOR
  - helper `list_deadlines_needing_alert` respeita `days_before`
  - auth obrigatória (401)

## Decisões de desenho

1. **Tabela dedicada** em vez de `User.custom_data` — User não tem JSON; tabela pequena e tipada.
2. **Sem envio** — digest é preview; `would_send` / `channels` só descrevem o que *seria* enviado.
3. **Quiet hours** armazenadas mas ainda não aplicadas no digest (campo pronto para o job futuro).

## Como validar

```bash
cd backend
pytest tests/test_notification_preferences.py -q
```

UI: `/settings` (JWT) → Alertas de prazos → Salvar.

## Próximos passos (fora deste MVP)

- Job/cron que chama `list_deadlines_needing_alert` e envia e-mail/WhatsApp
- Respeitar quiet hours no envio
- Marcar `Deadline.notification_sent` após envio bem-sucedido
- Unificar com a UI em `frontend/src/app/settings` se esse tree for o canônico
