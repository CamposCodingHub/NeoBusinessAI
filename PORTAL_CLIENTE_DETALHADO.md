# 👤 PORTAL DO CLIENTE - ESPECIFICAÇÃO

## Visão Geral
Interface exclusiva para clientes acompanharem processos, documentos e faturas de forma segura e transparente.

## Funcionalidades

### 1. Autenticação
- Login: CPF + senha ou magic link
- Token JWT com escopo limitado (só próprios dados)
- Session timeout: 30 minutos
- Recuperação senha via SMS/email

### 2. Dashboard Cliente
```
┌─────────────────────────────────────┐
│  Olá, [Nome Cliente]               │
├─────────────────────────────────────┤
│ 📁 Meus Processos (3)              │
│ 💰 Faturas Pendentes (R$ 2.500)    │
│ 📅 Próximo Prazo: 15/05/2025       │
│ 💬 Mensagens não lidas (2)         │
├─────────────────────────────────────┤
│ [Ver Processos] [Ver Faturas]      │
└─────────────────────────────────────┘
```

### 3. Processos
- Lista de casos do cliente
- Visualização prazos (read-only)
- Timeline do processo
- Documentos compartilhados (download)
- Status atualizado

### 4. Documentos
- Documentos vinculados aos processos
- Download apenas (não pode upload)
- Histórico de versões
- Visualização online (PDF viewer)

### 5. Faturas
- Lista todas faturas
- Status: paga, pendente, atrasada
- Download boleto/PIX
- Marcar como pago (notifica escritório)
- Histórico pagamentos

### 6. Comunicação
- Chat com advogado
- Histórico mensagens
- Enviar mensagem texto
- Anexar arquivo (para advogado)

## Modelos de Dados
```python
class ClientPortalUser:
    client_id, password_hash
    magic_link_token, magic_link_expires
    last_login, login_attempts
    is_active

class ClientSession:
    client_id, token
    created_at, expires_at
    ip_address, user_agent

class ClientActivityLog:
    client_id, action  # view_process, download_doc, etc
    resource_type, resource_id
    timestamp, ip_address
```

## Rotas API (/portal)
```python
POST /portal/auth/login          # Login CPF/senha
POST /portal/auth/magic-link     # Solicitar magic link
POST /portal/auth/verify         # Verificar magic link
GET  /portal/dashboard           # Dashboard cliente
GET  /portal/processes            # Lista processos
GET  /portal/processes/{id}       # Detalhes processo
GET  /portal/documents            # Documentos
GET  /portal/documents/{id}/download
GET  /portal/invoices             # Faturas
POST /portal/invoices/{id}/mark-paid
GET  /portal/chat/messages        # Histórico chat
POST /portal/chat/send           # Enviar mensagem
```

## Frontend (/portal/*)
```
/portal/login           - Página login
/portal/dashboard       - Dashboard principal
/portal/processes       - Lista processos
/portal/processes/[id]  - Detalhes processo
/portal/documents       - Documentos
/portal/invoices        - Faturas
/portal/chat            - Chat com advogado
```

## Segurança
- JWT scope: "portal" (limitado)
- CORS restrito
- Rate limiting: 100 req/hora
- Logs todos acessos (LGPD)
- Criptografia campos sensíveis

## Roadmap 4-6 Semanas
```
Semana 1: Backend auth + modelos
Semana 2: APIs portal
Semana 3: Frontend login + dashboard
Semana 4: Processos + documentos
Semana 5: Faturas + chat
Semana 6: Testes + segurança
```

## Estimativa
- Desenvolvimento: R$ 45.000

