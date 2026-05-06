# ⚖️ INTEGRAÇÃO COM TRIBUNAIS - PLANO DETALHADO

## Visão Geral
Sistema automatizado de coleta de jurisprudência e movimentações processuais diretamente dos tribunais brasileiros.

## Tribunais por Fase

### Fase 1: Superior (Semanas 1-6)
| Tribunal | Tecnologia | Dificuldade | Volume |
|----------|-----------|-------------|--------|
| STJ | Web Scraping | Média | 50k/ano |
| STF | Web Scraping | Média | 2k/ano |

### Fase 2: Grandes Estados (Semanas 7-14)
| Tribunal | Tecnologia | Dificuldade | Volume |
|----------|-----------|-------------|--------|
| TJSP | E-SAJ Scraping | Alta | 500k/ano |
| TRF-3 | API + Certificado | Média | 30k/ano |

### Fase 3: Nacional (Semanas 15-24)
- TRF-1, TRF-2, TRF-4, TRF-5
- TJMG, TJRS, TJPR, TJRJ
- TSE, TST

## Tecnologias

### Web Scraping
```python
# scrapers/base_scraper.py
from selenium import webdriver
from playwright.async_api import async_playwright

class TribunalScraper:
    async def search_decisions(self, query, filters):
        pass
    
    async def get_decision_details(self, decision_id):
        pass
    
    async def download_pdf(self, pdf_url):
        pass

# Implementações específicas
class STJScraper(TribunalScraper):
    BASE_URL = "https://scon.stj.jus.br/SCON/"
    
class TJSPScraper(TribunalScraper):
    BASE_URL = "https://esaj.tjsp.jus.br/cjsg/"
    # E-SAJ requer múltiplos requests e parsing complexo
```

### APIs Onde Disponíveis
```python
# APIs/documentadas
class TRF3API:
    BASE_URL = "https://api.trf3.jus.br/v1"
    AUTH_TYPE = "certificado"  # A1/A3
    
    def authenticate(self, cert_path, key_path):
        pass
```

## Infraestrutura

### VPS Scraping Dedicado
```bash
# Especificações mínimas
- CPU: 4 cores
- RAM: 8GB
- Storage: 100GB SSD
- Bandwidth: 1TB/mês
- IP: Fixo (para whitelist)
- Custo: ~R$ 200/mês
```

### Cron Jobs
```bash
# Sincronização diária
0 3 * * * python scripts/sync_tribunais.py --source=STJ
30 3 * * * python scripts/sync_tribunais.py --source=STF
0 4 * * * python scripts/sync_tribunais.py --source=TJSP

# Verificação integridade
0 */6 * * * python scripts/verify_sync.py
```

## Arquitetura de Dados

### Fluxo de Sincronização
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Tribunal  │────→│   Scraper   │────→│Normalização │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
┌─────────────┐     ┌─────────────┐     ┌───────▼───────┐
│  Notificação│←────│    Banco    │←────│  Validação    │
│  WhatsApp   │     │  PostgreSQL │     │   (IA/Regex)  │
└─────────────┘     └─────────────┘     └───────────────┘
```

### Normalização de Dados
```python
# Padronização campos
COURT_MAPPING = {
    'STJ': {'name': 'Superior Tribunal de Justiça', 'type': 'superior'},
    'TJSP': {'name': 'Tribunal de Justiça de SP', 'type': 'estadual'},
    # ...
}

RESULT_MAPPING = {
    'provimento': ['Provimento', 'Procedente', 'Parcial Procedente'],
    'improvimento': ['Improvimento', 'Improcedente', 'Extinto'],
    # ...
}
```

## Implementação Detalhada

### Semana 1-3: STJ
1. Análise estrutura SCON
2. Desenvolvimento scraper
3. Parser de ementas
4. Download PDFs
5. Testes

### Semana 4-6: STF
1. Análise portal STF
2. Scraper ADIs, ADCs
3. Parser documentos
4. Testes

### Semana 7-11: TJSP (Complexo)
1. Análise E-SAJ (formulários dinâmicos)
2. Múltiplos requests
3. Paginação
4. Parser HTML robusto
5. Rate limiting handling
6. Testes extensivos

### Semana 12-14: TRF-3 (API)
1. Certificado digital
2. Autenticação
3. Consumo API
4. Mapeamento endpoints

## Custos Operacionais

### Mensais (em produção)
| Item | Custo |
|------|-------|
| VPS Scraping | R$ 200 |
| Storage S3 | R$ 150-500 |
| Bandwidth | R$ 100 |
| IPs fixos | R$ 50 |
| Monitoramento | R$ 100 |
| **Total** | **R$ 600-950/mês** |

## Roadmap 24 Semanas
```
Mês 1: STJ + STF
Mês 2: TJSP (foco principal)
Mês 3: TRF-3 + outros TRFs
Mês 4: TJs grandes (MG, RS, RJ)
Mês 5: TJs restantes
Mês 6: Polimento + sync automático
```

## Estimativa Desenvolvimento
- 2 devs backend senior: R$ 25.000 × 2 × 6 meses = R$ 300.000
- 1 devops: R$ 20.000 × 6 meses = R$ 120.000
- **Total: R$ 420.000**

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Mudança layout tribunal | Alta | Alto | Monitoramento + alertas |
| CAPTCHA | Média | Alto | Soluções anti-CAPTCHA |
| Rate limiting | Alta | Médio | Delays + retry logic |
| Certificado expirar | Média | Alto | Monitoramento vencimento |

## Próximos Passos
1. Contratar VPS scraping
2. Implementar STJ (piloto)
3. Documentar padrões
4. Escala para demais tribunais

