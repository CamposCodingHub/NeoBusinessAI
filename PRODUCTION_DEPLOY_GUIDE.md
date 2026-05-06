# 🚀 Production Deploy Guide - LexScan IA

> Guia completo para deploy em produção com segurança enterprise

---

## 📋 PRE-DEPLOY CHECKLIST

### ✅ Segurança
- [ ] Todas as vulnerabilidades críticas corrigidas
- [ ] MFA implementado e testado
- [ ] Senhas criptografadas (AES-256)
- [ ] Rate limiting ativo (100 req/min)
- [ ] WAF Cloudflare configurado
- [ ] HTTPS/TLS 1.2+ obrigatório
- [ ] Security headers em todas as respostas
- [ ] Audit logging funcionando
- [ ] SIEM integration configurada

### ✅ Infraestrutura
- [ ] PostgreSQL com índices otimizados
- [ ] PgBouncer configurado (connection pooling)
- [ ] Redis Cache ativo
- [ ] Celery workers rodando
- [ ] Backups automáticos configurados
- [ ] Monitoramento (health checks) ativo
- [ ] Logs centralizados

### ✅ Aplicação
- [ ] Testes passando (>80% cobertura)
- [ ] Variáveis de ambiente configuradas
- [ ] Documentação API atualizada
- [ ] Frontend buildado sem erros
- [ ] OCR funcionando em produção
- [ ] IA respondendo corretamente

### ✅ Compliance
- [ ] Política de privacidade publicada
- [ ] Termos de serviço atualizados
- [ ] LGPD compliance verificado
- [ ] DPO (Data Protection Officer) designado

---

## 🏗️ ARQUITETURA DE PRODUÇÃO

```
┌─────────────────────────────────────────────────────────────┐
│                         CLOUDFLARE                           │
│  (DDoS Protection + WAF + SSL + CDN + Rate Limiting)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Frontend   │  │    Backend   │  │    Celery    │    │
│  │   (Next.js)  │  │   (FastAPI)  │  │   Workers    │    │
│  │   3 replicas │  │   3 replicas   │  │   2 workers  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│     PgBouncer    │    │      Redis       │
│   (Port 6432)    │    │   (Caching +     │
│  Connection Pool │    │     Queue)       │
└────────┬─────────┘    └──────────────────┘
         │
         ▼
┌──────────────────┐
│   PostgreSQL     │
│  (Primary +      │
│   Read Replica)  │
└──────────────────┘
```

---

## 🔧 STEP-BY-STEP DEPLOY

### 1. Preparação do Ambiente (30 min)

```bash
# Clonar repositório
git clone https://github.com/lexscan/lexscan-ia.git
cd lexscan-ia

# Verificar branch
# git checkout main
# git pull origin main

# Instalar dependências backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Instalar dependências frontend
cd ../frontend
npm install
```

### 2. Configuração de Variáveis de Ambiente (15 min)

Criar arquivo `.env.production` no backend:

```bash
# ========================================
# LEXSCAN IA - PRODUCTION ENV
# ========================================

# App
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here-32-chars

# Database (via PgBouncer)
DATABASE_URL=postgresql://user:pass@localhost:6432/lexscan
# Ou Neon/Railway:
# DATABASE_URL=postgresql://user:pass@neon-host.neon.tech/lexscan?sslmode=require

# Redis
REDIS_URL=redis://localhost:6379/0
# Ou Upstash:
# REDIS_URL=rediss://default:pass@upstash-url:6379

# AI APIs
GROQ_API_KEY=gsk_your_groq_key_here
OPENAI_API_KEY=sk-your-openai-key-here

# Firebase
FIREBASE_PROJECT_ID=lexscan-ia
FIREBASE_API_KEY=your-firebase-api-key

# Stripe (Pagamentos)
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@lexscan.ai
SMTP_PASS=your-app-password

# Cloudflare (WAF)
CLOUDFLARE_API_TOKEN=your-cloudflare-token

# SIEM (Opcional)
SIEM_PROVIDER=splunk  # splunk, datadog, elk, none
SIEM_ENDPOINT=https://your-siem-endpoint
SIEM_API_KEY=your-siem-api-key

# MFA Encryption
MFA_SECRET_KEY=your-32-char-secret-for-mfa

# Sentry (Error Tracking)
SENTRY_DSN=https://your-sentry-dsn
```

### 3. Configuração PostgreSQL (20 min)

```bash
# Conectar ao PostgreSQL
psql -U postgres -h your-db-host

# Criar banco de dados
CREATE DATABASE lexscan;

# Criar usuário (não use root)
CREATE USER lexscan_app WITH PASSWORD 'strong-password-here';
GRANT ALL PRIVILEGES ON DATABASE lexscan TO lexscan_app;

# Aplicar migrações
python -c "from database import init_db; init_db()"

# Criar índices otimizados
python database_optimizations.py

# Verificar índices
\d users
\d documents
\d deadlines
```

### 4. Configuração PgBouncer (15 min)

```bash
# Instalar
sudo apt-get update
sudo apt-get install pgbouncer

# Copiar configuração
sudo cp backend/pgbouncer/pgbouncer.ini /etc/pgbouncer/

# Criar arquivo de usuários
echo "\"lexscan_app\" \"strong-password-here\"" | sudo tee /etc/pgbouncer/userlist.txt

# Ajustar permissões
sudo chown pgbouncer:pgbouncer /etc/pgbouncer/userlist.txt
sudo chmod 600 /etc/pgbouncer/userlist.txt

# Iniciar
sudo systemctl enable pgbouncer
sudo systemctl start pgbouncer

# Verificar status
sudo systemctl status pgbouncer
```

### 5. Configuração Redis (10 min)

```bash
# Instalar
sudo apt-get install redis-server

# Copiar configuração
sudo cp backend/redis/redis.conf /etc/redis/

# Iniciar
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Testar
redis-cli ping
# Deve retornar: PONG
```

### 6. Deploy do Backend (15 min)

```bash
# Buildar Docker image
docker build -t lexscan-backend:latest -f backend/Dockerfile .

# Tag para registry
docker tag lexscan-backend:latest your-registry.com/lexscan-backend:v1.0.0

# Push
# docker push your-registry.com/lexscan-backend:v1.0.0

# Deploy no Kubernetes (exemplo)
# kubectl apply -f k8s/backend-deployment.yaml
# kubectl apply -f k8s/backend-service.yaml

# Ou usar Railway/Render (mais simples para MVP)
# railway login
# railway init
# railway up

# Verificar deploy
curl https://api.lexscan.ai/api/health
# Deve retornar: {"status": "healthy"}
```

### 7. Deploy do Frontend (10 min)

```bash
# Build
npm run build

# Verificar build
ls -la .next/

# Deploy Vercel (recomendado)
npm i -g vercel
vercel login
vercel --prod

# Ou deploy estático
# scp -r out/* user@server:/var/www/lexscan.ai/
```

### 8. Configuração Celery Workers (10 min)

```bash
# Iniciar worker
# cd backend
celery -A tasks worker --loglevel=info --concurrency=4 &

# Iniciar beat (scheduler)
celery -A tasks beat --loglevel=info &

# Ou usar systemd
sudo cp backend/celery/celery-worker.service /etc/systemd/system/
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
```

### 9. Configuração Cloudflare (15 min)

1. **Adicionar domínio:**
   - Acesse dash.cloudflare.com
   - Adicione `lexscan.ai`
   - Atualize nameservers no registrador

2. **Configurar DNS:**
   ```
   Type: A
   Name: api
   Content: <seu-backend-ip>
   Proxy: Enabled (orange cloud)
   ```

3. **Ativar WAF:**
   - Security → WAF
   - Importar regras do `CLOUDFLARE_WAF_CONFIG.md`

4. **SSL/TLS:**
   - Mode: Full (strict)
   - Always Use HTTPS: ON

### 10. Verificação Pós-Deploy (30 min)

```bash
# Health checks
curl https://api.lexscan.ai/api/health
curl https://api.lexscan.ai/api/status

# Testar autenticação
curl -X POST https://api.lexscan.ai/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'

# Testar upload de documento
curl -X POST https://api.lexscan.ai/api/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "user_email=test@example.com"

# Testar IA
curl -X POST https://api.lexscan.ai/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual é o prazo para recorrer?", "document_id": 1}'

# Testar MFA (se habilitado)
curl -X POST https://api.lexscan.ai/api/auth/mfa/validate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123", "token": "123456"}'
```

---

## 🔍 VERIFICAÇÕES DE SEGURANÇA

### Testes de Segurança

```bash
# 1. Testar proteção contra Path Traversal
curl -X POST https://api.lexscan.ai/api/documents/upload \
  -F "file=@../../../etc/passwd" \
  -F "user_email=test@example.com"
# Esperado: 400 Bad Request

# 2. Testar rate limiting
for i in {1..120}; do
  curl -s -o /dev/null -w "%{http_code}" https://api.lexscan.ai/api/health
done
# Esperado: Alguns 429 Too Many Requests

# 3. Testar CORS
curl -H "Origin: https://malicious-site.com" \
  https://api.lexscan.ai/api/documents
# Esperado: 403 Forbidden ou CORS error

# 4. Verificar headers de segurança
curl -I https://api.lexscan.ai/api/health
# Esperado: X-Content-Type-Options, X-Frame-Options, etc.
```

### Scan de Vulnerabilidades

```bash
# Usar OWASP ZAP (recomendado)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://api.lexscan.ai

# Ou usar nuclei
nuclei -u https://api.lexscan.ai -t cves/
```

---

## 📊 MONITORAMENTO PÓS-DEPLOY

### Dashboards de Monitoramento

**1. Health Status:**
```bash
curl https://api.lexscan.ai/api/monitoring/health
```

**2. Métricas:**
```bash
curl https://api.lexscan.ai/api/monitoring/metrics
```

**3. Alertas:**
```bash
curl https://api.lexscan.ai/api/monitoring/alerts
```

### Checklist Diário (Primeira Semana)

- [ ] Nenhum erro crítico nos logs
- [ ] Tempo de resposta < 500ms (p95)
- [ ] Taxa de erro < 1%
- [ ] Disponibilidade > 99.9%
- [ ] Backups automáticos funcionando
- [ ] Celery workers processando jobs
- [ ] Redis cache hit rate > 80%
- [ ] PostgreSQL connections < 80%

---

## 🚨 ROLLBACK PLAN

Se algo der errado:

```bash
# 1. Identificar versão estável anterior
# git log --oneline

# 2. Rollback do backend
kubectl rollout undo deployment/backend
# ou
# railway rollback

# 3. Rollback do frontend
vercel --rollback

# 4. Verificar se voltou ao normal
curl https://api.lexscan.ai/api/health

# 5. Investigar logs
# kubectl logs deployment/backend --previous
```

---

## 📞 SUPORTE E CONTATOS

**Emergências:**
- 🚨 P1 (Site fora): Discord/WhatsApp grupo tech
- 🔥 P2 (Funcionalidade crítica falhando): Email tech-lead
- ⚠️ P3 (Bug não crítico): GitHub Issues

**Documentação:**
- Runbook: notion.so/lexscan-runbook
- Playbooks: notion.so/lexscan-playbooks
- API Docs: api.lexscan.ai/docs

---

## ✅ POST-DEPLOY SIGN-OFF

**Assinaturas necessárias:**

- [ ] **CTO:** Code review completo, testes passando
- [ ] **Security Lead:** Scan de vulnerabilidades limpo
- [ ] **DevOps:** Infraestrutura estável, monitoring ativo
- [ ] **Product:** Funcionalidades core funcionando
- [ ] **CEO:** Aprovação final para go-live

**Data do Deploy:** ___/___/______  
**Versão:** v1.0.0  
**Responsável pelo Deploy:** _________________

---

> 🎉 **PARABÉNS!** O LexScan IA está agora em produção!

Lembre-se: *"Deploy é só o começo. Monitorar, otimizar e iterar é o jogo."*

---

*Deploy Guide Version 1.0 | May 2026*
