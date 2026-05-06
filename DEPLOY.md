# 🚀 Guia de Deploy em Produção - LexScan IA

**Versão:** 1.0.0  
**Última atualização:** 02/05/2026  
**Status:** Produção Ready ✅

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
4. [Deploy do Backend](#deploy-do-backend)
5. [Deploy do Frontend](#deploy-do-frontend)
6. [Configuração de Domínio](#configuração-de-domínio)
7. [Segurança](#segurança)
8. [Monitoramento](#monitoramento)
9. [Backup e Recuperação](#backup-e-recuperação)
10. [Checklist Final](#checklist-final)

---

## Visão Geral

### Arquitetura de Produção

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      Cloudflare / CDN                        │
│                (SSL, DDoS Protection, Cache)                │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      Vercel (Frontend)                       │
│              Next.js + Static/SSR + Edge Network            │
│              https://lexscan.ai / www.lexscan.ai            │
└─────────────────────────────────────────────────────────────┘
    │ API Calls
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Railway / Render (Backend)                │
│              FastAPI + Uvicorn + Gunicorn                     │
│              https://api.lexscan.ai                         │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                 Neon / Supabase (PostgreSQL)                 │
│              Database: lexscan_prod                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              Serviços Externos                              │
│  • Firebase Auth    • Stripe Payments                        │
│  • Groq API         • SendGrid / Gmail SMTP                  │
│  • Tesseract OCR    • Cloud Storage (S3/GCS)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Pré-requisitos

### Contas Necessárias

- [ ] **Vercel** (Frontend) - https://vercel.com
- [ ] **Railway** ou **Render** (Backend) - https://railway.app / https://render.com
- [ ] **Neon** ou **Supabase** (PostgreSQL) - https://neon.tech
- [ ] **Cloudflare** (DNS + SSL + CDN) - https://cloudflare.com
- [ ] **Firebase** (Auth) - https://console.firebase.google.com
- [ ] **Stripe** (Pagamentos) - https://stripe.com
- [ ] **Groq** (AI) - https://console.groq.com
- [ ] **SendGrid** ou **Amazon SES** (Email) - Opcional

### Ferramentas Locais

```bash
# Instalar CLI tools
npm i -g vercel
npm i -g @railway/cli  # ou usar dashboard web

# Git configurado
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"
```

---

## Configuração do Banco de Dados

### 1. Criar Banco Neon (PostgreSQL)

```bash
# Acesse https://console.neon.tech
# 1. Sign up / Login
# 2. Create New Project
# 3. Project Name: lexscan-production
# 4. Database Name: lexscan_prod
# 5. Region: São Paulo (sa-east-1) ou mais próximo

# Copiar connection string
# Exemplo: postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/lexscan_prod
```

### 2. Criar Tabelas

```bash
# Localmente, com a DATABASE_URL do Neon
export DATABASE_URL="postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/lexscan_prod"

cd backend
python -c "from database import init_db; init_db()"
```

Ou execute SQL direto no dashboard do Neon:

```sql
-- O SQL será gerado automaticamente pelo SQLAlchemy
-- Verifique se todas as tabelas foram criadas:
\dt
```

### 3. Configurar Pool de Conexões

No dashboard do Neon:
- Connection Pooler: **Ativado**
- Pool Size: **20**
- Use connection string do pooler para produção

---

## Deploy do Backend

### Opção 1: Railway (Recomendado)

#### 1.1 Preparar Projeto

```bash
# Criar railway.json
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4 --timeout 120",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
EOF
```

#### 1.2 Criar Procfile (alternativa)

```bash
cat > Procfile << 'EOF'
web: gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4 --timeout 120
EOF
```

#### 1.3 Deploy

```bash
# Login
railway login

# Inicializar projeto
railway init
# ? Project name: lexscan-backend
# ? Setup Environments: Yes
# ? Select Environment: production

# Deploy
railway up

# Ver logs
railway logs

# Abrir no browser
railway open
```

#### 1.4 Configurar Variáveis de Ambiente

No dashboard do Railway:

```bash
# Ir para: Project > Variables

# Adicionar todas as variáveis do .env:
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-inject se usar addon Postgres
GROQ_API_KEY=gsk_xxx
FIREBASE_PROJECT_ID=xxx
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."
FIREBASE_CLIENT_EMAIL=...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
CORS_ORIGINS=https://lexscan.ai,https://www.lexscan.ai
```

### Opção 2: Render

#### 2.1 Preparar render.yaml

```bash
cat > render.yaml << 'EOF'
services:
  - type: web
    name: lexscan-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: lexscan-db
          property: connectionString
      - key: GROQ_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.10.0

databases:
  - name: lexscan-db
    databaseName: lexscan_prod
    user: lexscan
    plan: standard
EOF
```

#### 2.2 Deploy via Dashboard

1. Acesse https://dashboard.render.com
2. New > Web Service
3. Connect GitHub repository
4. Configure:
   - Name: `lexscan-backend`
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 4`
5. Add Environment Variables (mesmas do Railway)
6. Deploy

---

## Deploy do Frontend

### Vercel (Recomendado)

#### 1. Preparar Configuração

```bash
# Criar vercel.json
cat > frontend/vercel.json << 'EOF'
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
EOF
```

#### 2. Configurar Environment Variables

```bash
# Criar .env.production no frontend/
cat > frontend/.env.production << 'EOF'
# Firebase
NEXT_PUBLIC_FIREBASE_API_KEY=xxx
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=lexscan-prod.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=lexscan-prod
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=lexscan-prod.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=xxx
NEXT_PUBLIC_FIREBASE_APP_ID=xxx

# API
NEXT_PUBLIC_API_URL=https://api.lexscan.ai
EOF
```

#### 3. Deploy

```bash
cd frontend

# Login
vercel login

# Deploy
vercel --prod

# Ou configure GitHub Integration:
# 1. Push para GitHub
# 2. Import projeto no Vercel
# 3. Configure env vars
# 4. Deploy automático em cada push
```

#### 4. Configurar Domínio Customizado

No dashboard do Vercel:
1. Project Settings > Domains
2. Add Domain: `lexscan.ai`
3. Add Domain: `www.lexscan.ai`
4. Siga as instruções de DNS

---

## Configuração de Domínio

### Cloudflare

#### 1. Registrar Domínio

```bash
# Compre lexscan.ai em:
# - Cloudflare Registrar
# - Namecheap
# - GoDaddy
# - Registro.br (para .com.br)
```

#### 2. Configurar DNS

No Cloudflare DNS:

```
Type    Name           Value                      TTL
─────────────────────────────────────────────────────────
A       lexscan.ai     76.76.21.21 (Vercel)       Auto
CNAME   www            cname.vercel-dns.com       Auto
A       api            34.200.50.50 (Railway)     Auto
```

#### 3. Configurar SSL/TLS

Cloudflare > SSL/TLS:
- Mode: **Full (strict)**
- Always Use HTTPS: **On**
- Automatic HTTPS Rewrites: **On**
- Minimum TLS Version: **1.2**

#### 4. Configurar Page Rules

```
# Redirect www para non-www
URL: www.lexscan.ai/*
Setting: Forwarding URL (301)
Destination: https://lexscan.ai/$1

# Cache API (opcional)
URL: api.lexscan.ai/static/*
Setting: Cache Level - Cache Everything
TTL: 1 hour
```

---

## Segurança

### Checklist de Segurança

- [ ] HTTPS obrigatório (HSTS)
- [ ] Headers de segurança configurados
- [ ] Rate limiting ativado
- [ ] CORS configurado corretamente
- [ ] Variáveis sensíveis em secrets
- [ ] Firebase Auth rules configuradas
- [ ] Stripe webhook signature verificado
- [ ] SQL injection protegido (ORM)
- [ ] XSS protection (React escape automático)

### Configurar CORS no Backend

```python
# backend/main.py

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lexscan.ai",
        "https://www.lexscan.ai",
        "https://*.vercel.app",  # Preview deployments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Trusted Hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "lexscan.ai",
        "www.lexscan.ai",
        "api.lexscan.ai",
        "*.railway.app",
        "*.render.com",
    ]
)
```

### Rate Limiting

```python
# backend/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Aplicar em endpoints
@app.post("/api/documents/upload")
@limiter.limit("10/minute")
async def upload_document(request: Request, ...):
    pass
```

### Security Headers

```python
# backend/main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Custom headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.firebaseapp.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://*.googleapis.com https://*.firebaseio.com https://*.groq.com"
    return response
```

---

## Monitoramento

### 1. Configurar Logs

Railway/Render: Logs já inclusos

Para análise avançada:
```bash
# Logtail (https://logtail.com)
# ou Papertrail (https://papertrailapp.com)
```

### 2. Uptime Monitoring

```bash
# UptimeRobot (https://uptimerobot.com)
# Monitorar:
# - https://lexscan.ai (frontend)
# - https://api.lexscan.ai/health (backend)
# - https://api.lexscan.ai (API)

# Configurar alertas:
# - Email: dev@lexscan.ai
# - Slack: #alerts
# - SMS: +55...
```

### 3. Analytics

```bash
# Vercel Analytics (built-in)
# Ativar no dashboard: Project > Analytics

# Google Analytics 4
# Adicionar GA ID no frontend

# Sentry (Error Tracking)
# npm install @sentry/nextjs
```

### 4. Health Check

```python
# backend/main.py

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "services": {
            "groq": check_groq_status(),
            "stripe": check_stripe_status(),
        }
    }
```

---

## Backup e Recuperação

### PostgreSQL (Neon)

Backups automáticos:
```bash
# Neon já faz backups automáticos
# Retention: 7 dias (free) / 30 dias (paid)

# Para backup manual:
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore:
psql $DATABASE_URL < backup_YYYYMMDD.sql
```

### Documentos (Storage)

Se usar armazenamento de arquivos:
```bash
# Opção 1: AWS S3
# - Criar bucket: lexscan-documents-prod
# - Versioning: Enabled
# - Lifecycle: Move to Glacier após 90 dias

# Opção 2: Cloudflare R2
# - Compatible with S3 API
# - Zero egress fees
```

### Firebase

```bash
# Backup Firestore:
# Usar Firebase Console > Export
# Ou: gcloud firestore export
```

---

## Checklist Final

### Pré-Deploy

- [ ] Todas as variáveis de ambiente configuradas
- [ ] Banco de dados inicializado com tabelas
- [ ] CORS configurado para domínio de produção
- [ ] SSL/TLS configurado (HTTPS obrigatório)
- [ ] Rate limiting ativado
- [ ] Logs configurados
- [ ] Health check endpoint funcionando

### Deploy Backend

- [ ] Código commitado no Git
- [ ] Deploy no Railway/Render executado
- [ ] Variáveis de ambiente no servidor
- [ ] Testar endpoint /health
- [ ] Testar endpoint /api/plans
- [ ] Verificar conexão com PostgreSQL

### Deploy Frontend

- [ ] Build local sem erros (`npm run build`)
- [ ] Deploy no Vercel executado
- [ ] Variáveis de ambiente NEXT_PUBLIC_* configuradas
- [ ] Domínio customizado configurado
- [ ] SSL/TLS funcionando
- [ ] Testar login
- [ ] Testar upload de documento

### Pós-Deploy

- [ ] Testar fluxo completo (login → upload → chat → PDF)
- [ ] Verificar responsividade mobile
- [ ] Testar Stripe (checkout de teste)
- [ ] Testar notificações email
- [ ] Verificar velocidade (PageSpeed Insights)
- [ ] Configurar UptimeRobot
- [ ] Configurar Analytics
- [ ] Documentar URLs de produção

### URLs Finais

```
🌐 Frontend: https://lexscan.ai
📊 Dashboard: https://lexscan.ai/dashboard
💰 Planos: https://lexscan.ai/pricing

🔌 API: https://api.lexscan.ai
📚 API Docs: https://api.lexscan.ai/docs
❤️ Health: https://api.lexscan.ai/health

🗄️ Database: postgres://... (Neon)
🔐 Auth: https://console.firebase.google.com
💳 Payments: https://dashboard.stripe.com
```

---

## 🚨 Troubleshooting

### Problema: CORS Error

```
Solução: Verificar CORS_ORIGINS no backend
Deve incluir: https://lexscan.ai (sem barra no final)
```

### Problema: 500 Internal Server Error

```bash
# Verificar logs
railway logs
# ou render logs

# Verificar DATABASE_URL
# Verificar GROQ_API_KEY
```

### Problema: Firebase Auth não funciona

```
1. Verificar Firebase config no frontend
2. Verificar Authorized Domains no Firebase Console
3. Adicionar: lexscan.ai e www.lexscan.ai
```

### Problema: Stripe Checkout falha

```
1. Verificar STRIPE_SECRET_KEY (deve ser sk_live_...)
2. Verificar STRIPE_PUBLISHABLE_KEY (deve ser pk_live_...)
3. Verificar webhook URL no Stripe Dashboard
```

---

## 📞 Suporte de Deploy

- 📧 **Email:** dev@lexscan.com.br
- 💬 **Slack:** #deploy-help
- 📚 **Docs:** https://docs.lexscan.ai/deploy

---

## 🎉 Parabéns!

Se você chegou até aqui, seu LexScan IA está **pronto para produção**! 🚀

**Próximos passos:**
1. Monitore os logs nas primeiras 24h
2. Colete feedback dos primeiros usuários
3. Acompanhe métricas de uso
4. Prepare-se para escalar! 📈

---

**Desenvolvido com ❤️ pela equipe LexScan IA**
