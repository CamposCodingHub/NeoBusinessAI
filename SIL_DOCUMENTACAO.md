# 🛡️ Security Intelligence Layer (SIL) - Documentação

## 📋 Visão Geral

O **Security Intelligence Layer (SIL)** é um sistema autônomo de auto-auditoria contínua em tempo real para proteção enterprise-grade da aplicação NeoBusiness AI.

### 🎯 Objetivos

- **Monitoramento 24/7**: Observação contínua de todas as atividades de login
- **Detecção em tempo real**: Identificação imediata de ameaças e anomalias
- **Proteção dinâmica**: Ajuste automático de defesas baseado em ameaças
- **Auto-correção**: Correção automática de falhas detectadas
- **Relatórios automáticos**: Geração periódica de relatórios de segurança
- **Simulação controlada**: Testes de penetração automatizados

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│              Security Intelligence Layer (SIL)          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Monitor   │  │  Detector   │  │    AI       │   │
│  │  (Login)    │  │ (Anomalias) │  │  (Análise)  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                │                │          │
│         └────────────────┴────────────────┘          │
│                          │                            │
│                   ┌──────▼──────┐                     │
│                   │    CORE     │                     │
│                   │ (Orquestr.) │                     │
│                   └──────┬──────┘                     │
│                          │                            │
│         ┌────────────────┼────────────────┐         │
│         │                │                │          │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  │
│  │   Alerts    │  │  Reporter   │  │ AutoCorrect │  │
│  │ (Notifica)  │  │ (Relatórios)│  │  (Correção) │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Módulos

### 1. **Core** (`core.py`)
Orquestrador principal que coordena todos os componentes.

**Responsabilidades:**
- Iniciar/parar monitoramento
- Gerenciar threads de monitoramento
- Coletar e agregar métricas
- Tomar decisões de segurança

**Ciclos:**
- Monitoramento: A cada 5 segundos
- Detecção: A cada 10 segundos
- Análise IA: A cada 1 minuto
- Auto-testes: A cada 1 hora
- Relatórios: A cada 24 horas

### 2. **Monitor** (`monitor.py`)
Monitoramento contínuo de tentativas de login.

**Funcionalidades:**
- Rastreamento de tentativas por IP
- Rastreamento de tentativas por usuário
- Bloqueio automático de IPs suspeitos
- Detecção de novos dispositivos
- Análise geográfica

**Buffers:**
- 1 minuto: Últimas 1000 tentativas
- 5 minutos: Últimas 5000 tentativas
- 1 hora: Últimas 50000 tentativas

### 3. **Detector** (`detector.py`)
Detecção inteligente de anomalias e padrões de ataque.

**Tipos de Detecção:**
- Brute force (força bruta)
- Distributed attack (ataque distribuído)
- Credential stuffing (senhas vazadas)
- Bot detection (detecção de bots)
- Rapid fire (tentativas rápidas)
- TOR exit nodes (rede TOR)
- Comportamento anômalo

**Níveis de Severidade:**
- `LOW`: Baixo risco
- `MEDIUM`: Médio risco
- `HIGH`: Alto risco
- `CRITICAL`: Crítico

### 4. **AI Engine** (`ai_engine.py`)
Inteligência artificial para análise preditiva.

**Capacidades:**
- Análise de risco em tempo real
- Previsão de ataques futuros
- Cálculo de score de segurança
- Análise comportamental de usuários
- Detecção de mudanças de padrão
- Aprendizado com incidentes

**Fatores de Risco:**
- Taxa de falha de login (25%)
- Múltiplos IPs (15%)
- Anomalia geográfica (20%)
- Anomalia de horário (15%)
- Anomalia de dispositivo (15%)
- Mudança comportamental (10%)

### 5. **Auto-Tester** (`autotest.py`)
Testes automáticos de segurança periódicos.

**Testes Realizados:**
- Login válido
- Login inválido
- Proteção brute force
- SQL injection
- XSS protection
- Proteção de rotas
- Rate limiting
- Isolamento multi-usuário

**Frequência:**
- Leve: A cada 6 horas
- Completo: A cada 24 horas
- Stress test: A cada 7 dias

### 6. **Alert Manager** (`alerts.py`)
Sistema de alertas e notificações.

**Canais:**
- Dashboard (sempre)
- Log (sempre)
- Email (warning+)
- SMS (critical)
- Webhook (error+)

**Níveis:**
- INFO: Informativo
- WARNING: Atenção
- ERROR: Erro
- CRITICAL: Crítico

### 7. **Reporter** (`reporter.py`)
Geração de relatórios automáticos.

**Tipos de Relatórios:**
- Diário (24h)
- Semanal (7 dias)
- Incidente (específico)
- Dashboard em tempo real

**Formatos:**
- JSON (API)
- PDF (exportação)
- Dashboard (web)

### 8. **Auto-Correct** (`autocorrect.py`)
Sistema de auto-correção de falhas.

**Ações:**
- Ajuste de rate limiting
- Bloqueio de IPs suspeitos
- Ativação de CAPTCHA
- Lockdown de emergência
- Reforço de defesas

### 9. **Simulator** (`simulator.py`)
Simulação controlada de ataques.

**Simulações:**
- Brute force
- Credential stuffing
- Distributed attack
- XSS
- SQL injection
- Rapid fire
- Stress test

### 10. **Dashboard API** (`dashboard_api.py`)
API REST para o painel de segurança.

**Endpoints:**
- `GET /sil/status` - Status do sistema
- `GET /sil/metrics` - Métricas em tempo real
- `GET /sil/dashboard` - Dados completos do dashboard
- `GET /sil/monitor/logins` - Estatísticas de login
- `GET /sil/analysis/threats` - Análise de ameaças
- `GET /sil/alerts` - Alertas ativos
- `POST /sil/simulations/run/{type}` - Executar simulação
- `GET /sil/reports/daily` - Relatório diário

---

## 🚀 Integração

### 1. Adicionar ao main.py

```python
# backend/main.py

from sil import get_sil
from sil.dashboard_api import router as sil_router

# Inicializar SIL
sil = get_sil()
sil.start_monitoring()

# Adicionar rotas
app.include_router(sil_router)
```

### 2. Integrar com auth_routes.py

```python
# backend/routes/auth_routes.py

from sil import get_sil

sil = get_sil()

@router.post("/login")
async def login(credentials: UserLoginSchema, request: Request):
    # ... código de login ...
    
    # Registrar no SIL
    sil.record_login_attempt(
        email=credentials.email,
        ip=get_client_ip(request),
        success=login_success,
        metadata={'user_agent': request.headers.get('User-Agent')}
    )
    
    # ... resto do código ...
```

### 3. Iniciar com aplicação

```python
# No startup do FastAPI

@app.on_event("startup")
async def startup_event():
    sil = get_sil()
    sil.start_monitoring()
    logger.info("🛡️ SIL iniciado")

@app.on_event("shutdown")
async def shutdown_event():
    sil = get_sil()
    sil.stop_monitoring()
    logger.info("🛑 SIL parado")
```

---

## 📊 Dashboard

### Acesso

```
GET http://localhost:8000/sil/dashboard
Authorization: Bearer <admin_token>
```

### Componentes

**Cards Principais:**
- Tentativas de login (1 min)
- Falhas de login (1 min)
- IPs bloqueados
- Usuários ativos
- Taxa de sucesso

**Gráficos:**
- Tendência de login (24h)
- Ataques por tipo
- Distribuição geográfica
- Timeline de eventos

**Alertas:**
- Alertas ativos
- Últimos eventos
- Anomalias detectadas

---

## 🧪 Simulações

### Executar Simulação

```bash
# Brute force
curl -X POST http://localhost:8000/sil/simulations/run/brute_force \
  -H "Authorization: Bearer <token>"

# Credential stuffing
curl -X POST http://localhost:8000/sil/simulations/run/credential_stuffing \
  -H "Authorization: Bearer <token>"

# Distributed attack
curl -X POST http://localhost:8000/sil/simulations/run/distributed \
  -H "Authorization: Bearer <token>"
```

### Stress Test

```bash
curl -X POST http://localhost:8000/sil/simulations/run/stress_test \
  -H "Authorization: Bearer <token>" \
  -d "{\"duration_minutes\": 5}"
```

---

## 📈 Métricas

### Score de Segurança

Calculado de 0 a 10 baseado em:
- Taxa de sucesso de login
- Anomalias detectadas
- IPs bloqueados
- Testes automatizados passados

### Status do Sistema

- `STABLE`: Seguro
- `ALERT`: Atenção necessária
- `CRITICAL`: Ataque em andamento
- `MAINTENANCE`: Manutenção

---

## 🚨 Alertas

### Configuração de Canais

```python
# Alertas por severidade
INFO → Dashboard + Log
WARNING → Dashboard + Log + Email
ERROR → Dashboard + Log + Email + Webhook
CRITICAL → Todos os canais + SMS
```

### Acknowledge

```bash
curl -X POST http://localhost:8000/sil/alerts/SEC-20240101-0001/acknowledge \
  -H "Authorization: Bearer <token>"
```

---

## 🔐 Segurança

### Lockdown de Emergência

```bash
curl -X POST http://localhost:8000/sil/control/emergency-lockdown \
  -H "Authorization: Bearer <token>"
```

**Ações:**
- Bloqueia todos os IPs suspeitos
- Ativa rate limiting estrito
- Força CAPTCHA para todos
- Desabilita novos registros
- Envia alertas críticos

---

## 📁 Estrutura de Arquivos

```
backend/sil/
├── __init__.py              # Inicialização do módulo
├── core.py                  # Orquestrador principal
├── monitor.py               # Monitoramento de login
├── detector.py              # Detecção de anomalias
├── ai_engine.py             # IA de análise
├── autotest.py              # Auto-testes
├── alerts.py                # Sistema de alertas
├── reporter.py              # Relatórios
├── autocorrect.py           # Auto-correção
├── simulator.py             # Simulação de ataques
└── dashboard_api.py         # API REST
```

---

## 🔧 Configuração

### Variáveis de Ambiente

```env
# SIL Configuration
SIL_ENABLED=true
SIL_LOG_LEVEL=INFO
SIL_ADMIN_EMAILS=admin@neobusiness.ai,security@neobusiness.ai
SIL_WEBHOOK_URL=https://hooks.slack.com/...

# Rate Limiting
SIL_MAX_ATTEMPTS_PER_IP=10
SIL_MAX_ATTEMPTS_PER_USER=5
SIL_BLOCK_DURATION=3600

# Auto-tests
SIL_AUTOTEST_ENABLED=true
SIL_AUTOTEST_INTERVAL=3600

# Reporting
SIL_DAILY_REPORT_ENABLED=true
SIL_REPORT_EMAILS=admin@neobusiness.ai
```

---

## 📝 Logs

### Formato

```
2024-01-01 12:00:00 - SIL - INFO - 🛡️ Security Intelligence Layer inicializado
2024-01-01 12:00:05 - SIL - INFO - 👁️ Login Monitor inicializado
2024-01-01 12:00:10 - SIL - WARNING - 🚨 ALERTA [SEC-20240101-0001] Brute Force Detectado
```

### Monitoramento

```bash
# Ver logs em tempo real
tail -f backend/logs/security.log | grep SIL
```

---

## 🎯 Casos de Uso

### 1. Detecção de Brute Force

1. Atacante tenta 20 logins em 1 minuto
2. SIL detecta padrão de alta velocidade
3. IP é bloqueado automaticamente
4. Alerta enviado para admins
5. Bloqueio registrado no audit trail

### 2. Ataque Distribuído

1. Múltiplos IPs tentam logar no mesmo usuário
2. SIL detecta padrão distribuído
3. Todos os IPs são bloqueados
4. Modo de proteção elevado ativado
5. Relatório gerado automaticamente

### 3. Login de Novo País

1. Usuário loga de país diferente
2. SIL detecta anomalia geográfica
2. Email de notificação enviado
4. Usuário verifica identidade
5. Novo país adicionado à baseline

---

## 📚 Referências

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **CIS Controls**: https://www.cisecurity.org/controls

---

## 👥 Contribuição

Para contribuir com o SIL:

1. Fork do repositório
2. Crie branch: `feature/sil-improvement`
3. Commit changes
4. Push para branch
5. Abra Pull Request

---

## 📄 Licença

© 2024 NeoBusiness AI. Todos os direitos reservados.

---

## 📞 Suporte

Para suporte técnico:
- Email: security@neobusiness.ai
- Dashboard: `/sil/dashboard`
- Documentação: `/docs`

---

**Versão:** 1.0.0  
**Última atualização:** 03/05/2026  
**Status:** Produção Ready
