# 📝 LexScan IA - Documentação da API

**Versão:** 1.0.0  
**Base URL:** `https://api.lexscan.ai/v1` ou `http://localhost:8000`  
**Formato:** JSON  
**Autenticação:** Firebase Auth (JWT)

---

## 📋 Índice

1. [Autenticação](#-autenticação)
2. [Documentos](#-documentos)
3. [Dashboard](#-dashboard)
4. [Chat](#-chat)
5. [Pagamentos](#-pagamentos)
6. [Notificações](#-notificações)
7. [Relatórios](#-relatórios)
8. [Erros](#-erros)

---

## 🔐 Autenticação

Todas as requisições (exceto login) requerem autenticação via Firebase.

### Headers

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

### Obter Token

```javascript
// Frontend - Firebase Auth
const user = firebase.auth().currentUser;
const token = await user.getIdToken();
```

---

## 📄 Documentos

### Upload e Processamento

```http
POST /api/documents/upload
```

**Content-Type:** `multipart/form-data`

**Parâmetros:**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `file` | File | Sim | Arquivo PDF ou imagem (max 50MB) |
| `manual_text` | string | Não | Texto manual (fallback OCR) |
| `user_email` | string | Sim | Email do usuário para controle de limites |

**Exemplo Request:**

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@peticao.pdf" \
  -F "user_email=advogado@email.com"
```

**Response Sucesso (200):**

```json
{
  "success": true,
  "document": {
    "id": 1,
    "filename": "peticao.pdf",
    "type": "peticao_inicial",
    "process_number": "12345-67.2024.8.26.0001",
    "parties": {
      "autor": "João Silva",
      "reu": "Empresa ABC Ltda",
      "advogado": "Dr. Carlos Mendes OAB/SP 123456"
    },
    "deadlines": [
      {
        "days": "15",
        "urgency": "high",
        "context": "Prazo para contestação"
      }
    ],
    "values": [
      {
        "value": "R$ 50.000,00",
        "context": "Valor da causa"
      }
    ],
    "court": "Vara do Trabalho de São Paulo",
    "summary": "Ação trabalhista pedindo rescisão indireta...",
    "analysis": "Documento bem formatado...",
    "uploaded_at": "2024-05-02T10:30:00",
    "status": "processed"
  }
}
```

**Response Erro - Limite Atingido (403):**

```json
{
  "success": false,
  "error": "Limite de documentos atingido",
  "limits": {
    "can_upload": false,
    "current_documents": 50,
    "documents_limit": 50,
    "documents_remaining": 0,
    "plan": "starter",
    "upgrade_required": true
  },
  "plans_url": "/pricing"
}
```

---

### Listar Documentos

```http
GET /api/documents?page=1&limit=20
```

**Parâmetros Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `page` | integer | 1 | Página atual |
| `limit` | integer | 20 | Itens por página (max 100) |
| `type` | string | - | Filtrar por tipo |
| `status` | string | - | Filtrar por status |

**Response (200):**

```json
{
  "success": true,
  "documents": [
    {
      "id": 1,
      "filename": "peticao.pdf",
      "type": "peticao_inicial",
      "process_number": "12345-67.2024.8.26.0001",
      "summary": "Ação trabalhista...",
      "deadlines_count": 2,
      "uploaded_at": "2024-05-02T10:30:00",
      "status": "processed"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 50,
    "pages": 3
  }
}
```

---

### Obter Documento

```http
GET /api/documents/{id}
```

**Response (200):**

```json
{
  "success": true,
  "document": {
    "id": 1,
    "filename": "peticao.pdf",
    "file_type": "application/pdf",
    "pages": 5,
    "ocr_method": "tesseract",
    "text_content": "Texto completo extraído...",
    "type": "peticao_inicial",
    "process_number": "12345-67.2024.8.26.0001",
    "parties": {
      "autor": "João Silva",
      "reu": "Empresa ABC Ltda",
      "advogado": "Dr. Carlos Mendes OAB/SP 123456"
    },
    "deadlines": [...],
    "values": [...],
    "analysis": "...",
    "summary": "...",
    "court": "...",
    "uploaded_at": "...",
    "status": "processed"
  }
}
```

---

### Deletar Documento

```http
DELETE /api/documents/{id}
```

**Response (200):**

```json
{
  "success": true,
  "message": "Documento removido com sucesso"
}
```

---

## 💬 Chat

### Chat com Documento

```http
POST /api/documents/{id}/chat
```

**Body:**

```json
{
  "question": "Quem é o autor da ação?",
  "context": "opcional - contexto adicional"
}
```

**Response (200):**

```json
{
  "success": true,
  "answer": "O autor da ação é João Silva, conforme consta na petição inicial.",
  "confidence": 0.95,
  "document_id": 1,
  "timestamp": "2024-05-02T11:00:00"
}
```

---

### Chat Geral

```http
POST /api/chat
```

**Body:**

```json
{
  "message": "O que você pode fazer?"
}
```

**Response (200):**

```json
{
  "success": true,
  "response": "Sou a LexScan IA, sua assistente jurídica! Posso...",
  "timestamp": "2024-05-02T11:00:00"
}
```

---

## 📊 Dashboard

### Estatísticas Gerais

```http
GET /api/dashboard
```

**Response (200):**

```json
{
  "success": true,
  "stats": {
    "total_documents": 50,
    "total_deadlines": 75,
    "urgent_deadlines": 12,
    "document_types": {
      "peticao_inicial": 20,
      "contestacao": 15,
      "recurso": 10
    },
    "last_upload": "2024-05-02T15:30:00"
  },
  "recent_documents": [...],
  "upcoming_deadlines": [...]
}
```

---

### Calendário de Prazos

```http
GET /api/calendar?year=2024&month=5
```

**Response (200):**

```json
{
  "success": true,
  "year": 2024,
  "month": 5,
  "deadlines": [
    {
      "day": 15,
      "deadlines": [
        {
          "id": 1,
          "document_id": 5,
          "document_name": "peticao.pdf",
          "days": 15,
          "urgency": "high",
          "context": "Prazo para contestação"
        }
      ]
    }
  ]
}
```

---

### Lista de Prazos

```http
GET /api/deadlines?urgency=high&page=1
```

**Parâmetros Query:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `urgency` | string | `high`, `medium`, `low` |
| `from` | date | Data inicial (YYYY-MM-DD) |
| `to` | date | Data final (YYYY-MM-DD) |
| `page` | integer | Página |
| `limit` | integer | Itens por página |

**Response (200):**

```json
{
  "success": true,
  "deadlines": [
    {
      "id": 1,
      "document_id": 5,
      "document_name": "peticao.pdf",
      "process_number": "12345-67.2024.8.26.0001",
      "days": 15,
      "urgency": "high",
      "context": "Prazo para contestação",
      "due_date": "2024-05-17",
      "created_at": "2024-05-02T10:30:00"
    }
  ],
  "pagination": {...}
}
```

---

## 💰 Pagamentos (Stripe)

### Listar Planos

```http
GET /api/plans
```

**Response (200):**

```json
{
  "success": true,
  "plans": [
    {
      "id": "starter",
      "name": "Starter",
      "price_brl": 29700,
      "price_formatted": "R$ 297,00/mês",
      "documents_limit": 50,
      "users_limit": 1,
      "features": ["OCR básico", "Resumo automático", "Suporte por email"],
      "popular": false,
      "contact_sales": false
    },
    {
      "id": "professional",
      "name": "Professional",
      "price_brl": 89700,
      "price_formatted": "R$ 897,00/mês",
      "documents_limit": 200,
      "users_limit": 5,
      "features": ["OCR avançado + IA", "Detecção de prazos", "Chat contextual"],
      "popular": true,
      "contact_sales": false
    }
  ],
  "stripe_configured": true,
  "stripe_public_key": "pk_test_..."
}
```

---

### Criar Checkout

```http
POST /api/checkout/create
```

**Body:**

```json
{
  "plan_id": "professional",
  "email": "advogado@email.com",
  "success_url": "https://lexscan.ai/dashboard?payment=success",
  "cancel_url": "https://lexscan.ai/pricing?payment=cancelled"
}
```

**Response Sucesso (200):**

```json
{
  "success": true,
  "session_id": "cs_test_...",
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
  "customer_id": "cus_..."
}
```

**Response Erro (400):**

```json
{
  "success": false,
  "error": "Stripe não configurado",
  "setup_instructions": [
    "1. Crie conta em https://stripe.com",
    "2. Obtenha suas chaves API",
    "3. Configure STRIPE_SECRET_KEY"
  ]
}
```

---

### Status da Assinatura

```http
GET /api/subscription/status?email=advogado@email.com
```

**Response (200):**

```json
{
  "success": true,
  "subscription_active": true,
  "plan": "professional",
  "plan_name": "Professional",
  "documents_limit": 200,
  "users_limit": 5,
  "current_period_end": 1717342800,
  "cancel_at_period_end": false,
  "current_usage": {
    "documents_uploaded": 45,
    "documents_remaining": 155
  }
}
```

---

### Verificar Limites

```http
GET /api/user/limits?email=advogado@email.com
```

**Response (200):**

```json
{
  "success": true,
  "limits": {
    "can_upload": true,
    "current_documents": 45,
    "documents_limit": 200,
    "documents_remaining": 155,
    "plan": "professional",
    "plan_name": "Professional",
    "subscription_active": true,
    "upgrade_required": false
  }
}
```

---

### Cancelar Assinatura

```http
POST /api/subscription/cancel
```

**Body:**

```json
{
  "email": "advogado@email.com"
}
```

**Response (200):**

```json
{
  "success": true,
  "message": "Assinatura cancelada com sucesso"
}
```

---

## 📧 Notificações

### Testar Conexão SMTP

```http
GET /api/notifications/test
```

**Response (200):**

```json
{
  "success": true,
  "smtp_connected": true,
  "message": "Conexão SMTP estabelecida com sucesso"
}
```

---

### Enviar Email de Teste

```http
POST /api/notifications/send-test
```

**Body:**

```json
{
  "to_email": "advogado@email.com"
}
```

**Response (200):**

```json
{
  "success": true,
  "message_id": "<message-id>",
  "message": "Email de teste enviado com sucesso"
}
```

---

### Verificar Prazos e Notificar

```http
POST /api/notifications/check-deadlines
```

**Body:**

```json
{
  "email": "advogado@email.com"
}
```

**Response (200):**

```json
{
  "success": true,
  "notifications_sent": 3,
  "notifications": [
    {
      "document_id": 5,
      "deadline": "15 dias - Contestação",
      "urgency": "high",
      "email_sent": true
    }
  ],
  "message": "3 notificações enviadas para advogado@email.com"
}
```

---

## 📄 Relatórios

### Exportar PDF do Documento

```http
GET /api/documents/{id}/report
```

**Headers:**

```http
Accept: application/pdf
```

**Response:**

```
Content-Type: application/pdf
Content-Disposition: attachment; filename=relatorio_peticao.pdf

[Binary PDF data]
```

---

### Exportar Relatório do Dashboard

```http
GET /api/reports/dashboard
```

**Headers:**

```http
Accept: application/pdf
```

**Response:**

```
Content-Type: application/pdf
Content-Disposition: attachment; filename=relatorio_dashboard_20240502.pdf

[Binary PDF data]
```

---

## ⚠️ Erros

### Códigos de Status HTTP

| Código | Significado |
|--------|-------------|
| 200 | Sucesso |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Sem permissão (limite atingido) |
| 404 | Recurso não encontrado |
| 422 | Erro de validação |
| 429 | Muitas requisições (rate limit) |
| 500 | Erro interno do servidor |

---

### Formatos de Erro

**Erro de Validação (422):**

```json
{
  "success": false,
  "error": "Dados inválidos",
  "details": {
    "email": ["Campo obrigatório"],
    "file": ["Arquivo muito grande (max 50MB)"]
  }
}
```

**Erro de Autenticação (401):**

```json
{
  "success": false,
  "error": "Não autenticado",
  "message": "Token inválido ou expirado"
}
```

**Erro de Limite (403):**

```json
{
  "success": false,
  "error": "Limite de documentos atingido",
  "current": 50,
  "limit": 50,
  "upgrade_url": "/pricing"
}
```

**Erro Interno (500):**

```json
{
  "success": false,
  "error": "Erro interno do servidor",
  "request_id": "uuid-para-debug",
  "message": "Ocorreu um erro inesperado. Tente novamente."
}
```

---

## 🔧 Webhooks

### Stripe Webhook

```http
POST /api/webhook/stripe
```

**Headers:**

```http
Stripe-Signature: t=1234567890,v1=signature
```

**Eventos Suportados:**

- `checkout.session.completed` - Pagamento confirmado
- `invoice.payment_failed` - Pagamento falhou
- `customer.subscription.deleted` - Assinatura cancelada

**Response:**

```json
{
  "received": true
}
```

---

## 📚 Exemplos de Uso

### Fluxo Completo: Upload → Chat → PDF

```javascript
// 1. Upload documento
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('user_email', 'advogado@email.com');

const upload = await fetch('/api/documents/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const { document } = await upload.json();

// 2. Chat sobre o documento
const chat = await fetch(`/api/documents/${document.id}/chat`, {
  method: 'POST',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ question: 'Quem é o autor?' })
});

const { answer } = await chat.json();
console.log(answer); // "O autor é João Silva..."

// 3. Exportar PDF
const pdf = await fetch(`/api/documents/${document.id}/report`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const blob = await pdf.blob();
const url = URL.createObjectURL(blob);
window.open(url);
```

---

### Fluxo: Assinatura

```javascript
// 1. Listar planos
const plans = await fetch('/api/plans').then(r => r.json());

// 2. Criar checkout
const checkout = await fetch('/api/checkout/create', {
  method: 'POST',
  headers: { 
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    plan_id: 'professional',
    email: 'advogado@email.com',
    success_url: window.location.origin + '/dashboard?payment=success',
    cancel_url: window.location.origin + '/pricing?payment=cancelled'
  })
});

const { checkout_url } = await checkout.json();

// 3. Redirecionar para Stripe
window.location.href = checkout_url;
```

---

## 📝 Changelog da API

### v1.0.0 (2024-05-02)
- ✅ API inicial
- ✅ Endpoints de documentos
- ✅ Endpoints de dashboard
- ✅ Endpoints de pagamentos
- ✅ Endpoints de notificações
- ✅ Exportação PDF
- ✅ Chat contextual

---

## 💬 Suporte da API

- 📧 **Email:** api@lexscan.com.br
- 📚 **Docs:** [api.lexscan.ai/docs](https://api.lexscan.ai/docs)
- 🔧 **Status:** [status.lexscan.ai](https://status.lexscan.ai)

---

**© 2024 LexScan IA - Todos os direitos reservados**
