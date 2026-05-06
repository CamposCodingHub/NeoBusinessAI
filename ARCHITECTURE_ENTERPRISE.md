# 🏗️ ARQUITETURA ENTERPRISE NEOBUSINESS AI

**Versão:** 2.0.0 Enterprise  
**Status:** Implementação em andamento

---

## 📁 ESTRUTURA DE DIRETÓRIOS

```
neobusiness-ai/
├── apps/
│   ├── api/                    # Backend FastAPI
│   │   ├── core/              # Configurações, database, security
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes (modulares)
│   │   │   ├── v1/
│   │   │   │   ├── auth/
│   │   │   │   ├── billing/
│   │   │   │   ├── documents/
│   │   │   │   ├── legal/
│   │   │   │   └── ai/
│   │   ├── services/          # Business logic
│   │   ├── middleware/        # Custom middleware
│   │   ├── tasks/             # Celery tasks
│   │   └── utils/             # Helpers
│   │
│   ├── web/                    # Frontend Next.js
│   │   ├── app/
│   │   │   ├── (auth)/        # Rotas de autenticação
│   │   │   ├── (dashboard)/   # Rotas protegidas
│   │   │   ├── (public)/      # Rotas públicas
│   │   │   └── api/           # API routes (Next.js)
│   │   ├── components/
│   │   │   ├── ui/            # Shadcn/UI components
│   │   │   ├── auth/          # Auth components
│   │   │   ├── billing/       # Billing components
│   │   │   └── features/      # Feature components
│   │   ├── lib/
│   │   │   ├── auth/          # Auth utilities
│   │   │   ├── api/           # API client
│   │   │   └── utils/         # Helpers
│   │   └── hooks/             # Custom React hooks
│   │
│   └── admin/                 # Admin panel separado
│       ├── app/
│       ├── components/
│       └── lib/
│
├── services/
│   ├── storage/               # Storage service (S3/R2)
│   ├── email/                 # Email service
│   ├── billing/               # Billing service (Mercado Pago)
│   └── ai/                    # AI service integration
│
├── infrastructure/
│   ├── docker/                # Docker configs
│   ├── kubernetes/            # K8s manifests
│   └── terraform/             # IaC
│
├── scripts/
│   ├── setup/                 # Setup scripts
│   ├── migration/             # DB migrations
│   └── seed/                  # Seed data
│
└── docs/
    ├── api/                   # API documentation
    ├── architecture/           # Architecture docs
    └── deployment/            # Deployment guides
```

---

## 🔐 PRINCÍPIOS DE ARQUITETURA

### 1. **Separation of Concerns**
- API, Web e Admin são aplicações separadas
- Business logic em services layer
- Database models isolados de API

### 2. **Multi-Tenant First**
- Todo código é tenant-aware por padrão
- Isolamento em todas as camadas
- Row Level Security no banco

### 3. **Security by Design**
- Autenticação obrigatória em tudo
- RBAC granular
- Rate limiting por padrão

### 4. **Scalability**
- Stateless APIs
- Horizontal scaling ready
- Cache estratégico

### 5. **Observability**
- Structured logging
- Metrics por padrão
- Tracing distribuído

---

## 🗄️ DATABASE ARCHITECTURE

### Schema Multi-Tenant

```sql
-- Users (com tenant_id)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    subscription_tier VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Documents (isolados por tenant)
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    file_path VARCHAR(500) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    plan_tier VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    external_id VARCHAR(255), -- Mercado Pago ID
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Row Level Security (RLS)

```sql
-- Habilitar RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: usuários só veem documentos do próprio tenant
CREATE POLICY tenant_isolation ON documents
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

---

## 🔐 SECURITY ARCHITECTURE

### Authentication Flow

```
1. User faz login
   ↓
2. Backend valida credenciais
   ↓
3. Gera access_token (15min) + refresh_token (7 dias)
   ↓
4. Armazena device info + IP
   ↓
5. Retorna tokens + device_id
   ↓
6. Frontend armazena em httpOnly cookies
```

### Token Strategy

- **Access Token:** 15 minutos, JWT, contém user_id + role + tenant_id
- **Refresh Token:** 7 dias, rotativo, armazenado em banco
- **Device Tracking:** Cada refresh token associado a device_id

### Rate Limiting

```
- Login: 5 tentativas / 15 minutos / IP
- API: 1000 requests / minuto / tenant
- AI: 100 requests / minuto / usuário
- Upload: 10 uploads / hora / usuário
```

---

## 💳 BILLING ARCHITECTURE

### Mercado Pago Integration

```
1. User escolhe plano
   ↓
2. Frontend chama API checkout
   ↓
3. Backend cria preferência Mercado Pago
   ↓
4. Mercado Pago retorna URL pagamento
   ↓
5. User paga
   ↓
6. Mercado Pago envia webhook
   ↓
7. Backend valida webhook (assinatura)
   ↓
8. Atualiza subscription status
   ↓
9. Libera features do plano
```

### Webhook Security

```python
def validate_webhook(signature: str, payload: bytes) -> bool:
    """
    Valida assinatura do webhook Mercado Pago
    """
    secret = settings.mercado_pago_webhook_secret
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## 🧠 AI ARCHITECTURE

### Secure AI Pipeline

```
1. User envia prompt
   ↓
2. Sanitização (anti prompt injection)
   ↓
3. Context injection (tenant-specific)
   ↓
4. Rate limit check
   ↓
5. Cost limit check
   ↓
6. AI generation
   ↓
7. Output sanitization
   ↓
8. Audit log
   ↓
9. Return response
```

### Anti Prompt Injection

```python
def sanitize_prompt(prompt: str) -> str:
    """
    Remove tentativas de prompt injection
    """
    # Detecta padrões maliciosos
    malicious_patterns = [
        'ignore previous instructions',
        'forget everything',
        'system prompt',
        'override',
        'bypass',
    ]
    
    for pattern in malicious_patterns:
        if pattern.lower() in prompt.lower():
            raise SecurityException("Prompt injection detected")
    
    return prompt
```

---

## 📊 OBSERVABILITY ARCHITECTURE

### Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram

# Request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# AI token usage
ai_tokens_used = Counter(
    'ai_tokens_used',
    'Total AI tokens consumed',
    ['tenant_id', 'model']
)

# Response time histogram
http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['endpoint']
)
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "user_action",
    action="document_upload",
    user_id=user.id,
    tenant_id=user.tenant_id,
    document_id=document.id,
    file_size=len(file_content),
    ip_address=request.client.host
)
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

### Environments

- **Development:** Docker Compose local
- **Staging:** Kubernetes cluster (GKE/AKS)
- **Production:** Kubernetes multi-region

### Infrastructure

```
- API: HorizontalPodAutoscaler (2-20 pods)
- Web: Cloudflare CDN + Edge functions
- Database: PostgreSQL HA (primary + 2 replicas)
- Cache: Redis Cluster
- Storage: R2/S3 com lifecycle policies
- Queue: Redis + Celery workers
```

---

## 📝 NEXT STEPS

1. ✅ Criar estrutura de diretórios
2. ⏳ Implementar core models
3. ⏳ Implementar auth service
4. ⏳ Implementar tenant middleware
5. ⏳ Implementar billing service
6. ⏳ Implementar AI service
7. ⏳ Implementar observability
8. ⏳ Deploy staging
9. ⏳ E2E tests
10. ⏳ Production deployment
