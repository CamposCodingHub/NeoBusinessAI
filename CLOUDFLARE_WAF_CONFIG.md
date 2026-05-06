# 🛡️ Cloudflare WAF Configuration - LexScan IA

## 📋 Configuração de Web Application Firewall

### 1. DNS Settings

```
Type: A
Name: api.lexscan.ai
Content: <SEU_BACKEND_IP>
Proxy Status: Proxied (orange cloud)
TTL: Auto
```

### 2. SSL/TLS Settings

```
SSL/TLS Mode: Full (strict)
Always Use HTTPS: ON
Automatic HTTPS Rewrites: ON
TLS 1.3: ON
Minimum TLS Version: 1.2
```

### 3. Security Level

```
Security Level: High
Challenge Passage: 30 minutes
```

### 4. WAF Rules (Firewall Rules)

#### Rule 1: Block Known Bad IPs
```
Expression: (ip.src in $cf.blocklist)
Action: Block
```

#### Rule 2: Rate Limiting API
```
Expression: (http.request.uri.path contains "/api/")
Action: Rate Limit
Requests: 100 per minute
Action: Block for 1 hour
```

#### Rule 3: Block Countries (High Risk)
```
Expression: (ip.geoip.country in {"CN" "RU" "KP" "IR"})
Action: Challenge (JS Challenge)
```

#### Rule 4: Protect Admin Endpoints
```
Expression: (http.request.uri.path contains "/admin" or http.request.uri.path contains "/internal")
Action: Challenge
```

#### Rule 5: Block SQL Injection
```
Expression: (
  http.request.uri.query contains "union" or
  http.request.uri.query contains "select" or
  http.request.uri.query contains "drop" or
  http.request.uri.query contains "insert" or
  http.request.uri.query contains "delete"
)
Action: Block
```

#### Rule 6: Block Path Traversal
```
Expression: (
  http.request.uri.path contains "../" or
  http.request.uri.path contains "..\\" or
  http.request.uri.path contains "%2e%2e%2f"
)
Action: Block
```

### 5. DDoS Protection

```
DDoS Protection: ON
Automatic DDoS Mitigation: ON
Sensitivity: High
```

### 6. Bot Management

```
Bot Fight Mode: ON
Super Bot Fight Mode: ON
Definitely Automated: Block
Verified Bots: Allow
```

### 7. Page Rules

#### Rule 1: Cache Static Assets
```
URL: *lexscan.ai/static/*
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 7 days
  - Browser Cache TTL: 1 day
```

#### Rule 2: Security Headers
```
URL: *lexscan.ai/*
Settings:
  - Security Headers: ON
  - HSTS: max-age=31536000; includeSubDomains; preload
```

### 8. API Shield

```
API Shield: ON
Schema Validation: ON
Client-side Certificate: ON
```

### 9. Terraform Configuration (Opcional)

```hcl
# cloudflare.tf
resource "cloudflare_zone" "lexscan" {
  zone = "lexscan.ai"
}

resource "cloudflare_record" "api" {
  zone_id = cloudflare_zone.lexscan.id
  name    = "api"
  value   = var.backend_ip
  type    = "A"
  proxied = true
}

resource "cloudflare_firewall_rule" "rate_limit_api" {
  zone_id     = cloudflare_zone.lexscan.id
  description = "Rate limit API requests"
  filter_id   = cloudflare_filter.rate_limit_api.id
  action      = "block"
}

resource "cloudflare_filter" "rate_limit_api" {
  zone_id = cloudflare_zone.lexscan.id
  expression = "(http.request.uri.path contains \"/api/\")"
}
```

### 10. Monitoring

```
Security Events: Enable notifications
Web Analytics: ON
Security Center: Review weekly
```

---

## 🔧 Implementação

### Passo 1: Configurar DNS
1. Acesse Cloudflare Dashboard
2. Adicione o domínio `lexscan.ai`
3. Atualize nameservers no registrador
4. Aguarde propagação (até 24h)

### Passo 2: Ativar WAF
1. Security → WAF
2. Criar regras conforme acima
3. Testar com Modo "Simulate" primeiro

### Passo 3: Verificar
```bash
# Testar proteção
curl -I https://api.lexscan.ai/api/documents

# Deve retornar:
# CF-RAY: <id> (indica que passou pelo Cloudflare)
# cf-cache-status: DYNAMIC
```

---

## 📊 Métricas de Segurança

| Métrica | Target | Alerta |
|---------|--------|--------|
| Requests bloqueados | < 1% | > 5% |
| Rate limit hits | < 0.1% | > 1% |
| DDoS mitigados | 100% | N/A |
| SSL handshake time | < 100ms | > 200ms |

---

**Status:** ✅ Configurado e pronto para deploy
