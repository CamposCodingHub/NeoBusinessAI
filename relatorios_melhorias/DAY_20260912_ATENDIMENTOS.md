# Atendimentos / contact log
## 12/09/2026 — tick diurno (~15:10)

### Dor
Histórico de ligações e WhatsApp fica no celular pessoal; equipe não sabe o que foi combinado.

### Entrega
- Modelo `ClientContactLog`
- API JWT `GET/POST /contacts/logs` (canais: phone, whatsapp, email, in_person, other)
- UI `/dashboard/atendimentos`
- Testes + QA simulator + router guard

### Limite
Não grava chamada nem sincroniza WhatsApp Business API.
