# 📋 ESPECIFICAÇÃO DOS 4 NOVOS MÓDULOS - JURISFLOW AI

## Resumo Executivo

### Módulo 1: Pesquisa Jurisprudencial por IA
**Tempo estimado:** 10-12 semanas | **Time:** 3 devs backend, 2 devs frontend

**Funcionalidades:**
- Busca em STJ, STF, TJSP, TRFs por linguagem natural
- IA analisa tendências e gera trechos prontos
- Filtros por tribunal, data, resultado
- Citações formatadas (ABNT/OAB)
- Dashboard de análise com gráficos

**Modelos de Dados:**
- `JurisprudenciaSource` (fontes/tribunais)
- `JurisprudenciaDecision` (acórdãos)
- `JurisprudenciaSearchHistory` (histórico)
- `JurisprudenciaSnippet` (trechos salvos)
- `JurisprudenciaTendencyReport` (relatórios)

**Rotas API:**
- GET/POST `/jurisprudencia/sources`
- POST `/jurisprudencia/search`
- POST `/jurisprudencia/search/ai-analysis`
- POST `/jurisprudencia/snippets/save`
- POST `/jurisprudencia/reports/tendency`

---

### Módulo 2: Gestão de Equipe e Tarefas
**Tempo estimado:** 8-10 semanas | **Time:** 2 devs backend, 2 devs frontend

**Funcionalidades:**
- Cadastro de advogados/estagiários/assistentes
- Hierarquia (sócio → advogado → estagiário)
- Atribuição de tarefas por processo
- Painel gerencial com KPIs
- Onboarding automatizado
- Base de conhecimento interna

**Perfis de Acesso:**
- Sócio/Admin: Acesso total
- Advogado Sênior: Gerencia sua equipe
- Advogado: Processos próprios
- Estagiário: Read-only + tarefas

**Modelos de Dados:**
- `TeamMember` (membros da equipe)
- `Task` (tarefas)
- `TaskComment` (comentários)
- `TimeEntry` (registro de horas)
- `OnboardingChecklist` (checklists)
- `KnowledgeBaseArticle` (base de conhecimento)
- `TeamPerformanceMetric` (métricas)

**Rotas API:**
- GET/POST `/team/members`
- GET/POST `/team/tasks`
- GET `/team/dashboard/manager`
- GET/POST `/team/onboarding/checklists`
- GET/POST `/team/knowledge-base`

---

### Módulo 3: Fila de Atendimento Inteligente
**Tempo estimado:** 6-8 semanas | **Time:** 2 devs backend, 1 dev frontend

**Funcionalidades:**
- Chatbot filtra perguntas simples (andamento, prazos)
- Fila priorizada para atendimento humano
- Classificação automática: urgente, financeiro, processual
- SLA monitoring (alerta se >X horas sem resposta)
- Dashboard de atendimento para advogado

**Modelos de Dados (extensão do WhatsApp):**
- `ChatQueue` (fila de mensagens)
- `ChatClassification` (classificação IA)
- `SLAMonitor` (monitoramento de SLA)

**Rotas API:**
- GET `/whatsapp/queue` (fila de atendimento)
- POST `/whatsapp/queue/classify` (classificar mensagem)
- GET `/whatsapp/queue/stats` (estatísticas SLA)
- POST `/whatsapp/queue/escalate` (escalar para humano)

---

### Módulo 4: Marketing OAB-Compliance
**Tempo estimado:** 6-8 semanas | **Time:** 2 devs backend, 2 devs frontend

**Funcionalidades:**
- Email marketing educativo (conforme OAB)
- Segmentação de clientes por área
- Sequência automática de relacionamento
- Pesquisa de satisfação automática
- Funil de captação: lead → consulta → contrato
- Qualificação automática de leads
- Auditoria de compliance OAB

**Restrições OAB Implementadas:**
- Sem publicidade direta (proibida)
- Conteúdo educativo apenas
- Sem promessas de resultado
- Sem captação agressiva
- Registro de todas comunicações

**Modelos de Dados:**
- `MarketingCampaign` (campanhas)
- `EmailSequence` (sequências)
- `Lead` (leads)
- `ClientSegment` (segmentos)
- `SatisfactionSurvey` (pesquisas)
- `OABComplianceLog` (auditoria)

**Rotas API:**
- GET/POST `/marketing/campaigns`
- GET/POST `/marketing/sequences`
- POST `/marketing/sequences/trigger`
- GET `/marketing/funnel/stats`
- POST `/marketing/surveys/send`

---

## PORTAL DO CLIENTE (Detalhamento Completo)

### Funcionalidades:
1. **Login separado** (token JWT diferente)
2. **Dashboard do Cliente:**
   - Processos em andamento (seus casos)
   - Próximos prazos (visão read-only)
   - Faturas pendentes
   - Mensagens não lidas
3. **Processos:**
   - Lista de processos do cliente
   - Visualização de prazos (não pode editar)
   - Documentos do processo (download)
   - Timeline do caso
4. **Documentos:**
   - Documentos compartilhados
   - Download (não pode upload)
5. **Faturas:**
   - Lista de faturas
   - Visualizar boleto/PIX
   - Marcar como pago (notifica escritório)
   - Histórico de pagamentos
6. **Comunicação:**
   - Chat com advogado (WhatsApp integrado)
   - Mensagens anteriores
   - Enviar mensagem (texto/arquivo)

### Segurança:
- Autenticação via CPF + senha ou magic link
- Token com escopo limitado (só vê seus dados)
- Logs de acesso (LGPD compliance)
- Session timeout: 30 minutos

### Modelos de Dados:
- `ClientPortalUser` (usuário do portal)
- `ClientSession` (sessões ativas)
- `ClientActivityLog` (logs de acesso)

### Rotas API:
- POST `/portal/auth/login`
- GET `/portal/dashboard`
- GET `/portal/processes`
- GET `/portal/processes/{id}`
- GET `/portal/documents`
- GET `/portal/invoices`
- POST `/portal/chat/send`
- GET `/portal/chat/messages`

### Frontend:
- `/portal/login` - Login do cliente
- `/portal/dashboard` - Dashboard
- `/portal/processes` - Processos
- `/portal/documents` - Documentos
- `/portal/invoices` - Faturas
- `/portal/chat` - Chat

---

## INTEGRAÇÃO COM TRIBUNAIS (Plano Detalhado)

### Fase 1: Fundação (Semanas 1-4)
**Tribunais:** STJ + STF
**Tecnologia:** Web Scraping (Selenium/Playwright)
**Infraestrutura:** VPS dedicado para scraping

#### Implementação STJ:
```python
# scrapers/stj_scraper.py
class STJScraper:
    BASE_URL = "https://scon.stj.jus.br/SCON/"
    
    def search_decisions(self, query, date_from, date_to):
        # Implementar busca no formulário SCON
        # Parsear resultados
        # Extrair ementas e inteiro teor
        pass
    
    def get_decision_details(self, decision_number):
        # Buscar detalhes completos
        # Download PDF se disponível
        pass
```

#### Implementação STF:
```python
# scrapers/stf_scraper.py  
class STFScraper:
    BASE_URL = "http://portal.stf.jus.br/jurisprudencia/"
    # Similar ao STJ
```

### Fase 2: Escala (Semanas 5-10)
**Tribunais:** TJSP + TRF-3
**Desafio:** TJSP usa E-SAJ (complexo)

#### Implementação TJSP:
```python
# scrapers/tjsp_scraper.py
class TJSPScraper:
    BASE_URL = "https://esaj.tjsp.jus.br/cjsg/"
    
    def search_decisions(self, query):
        # E-SAJ requer múltiplos requests
        # Parser de HTML complexo
        # Paginação dinâmica
        pass
```

#### API TRF-3:
- Usa certificado digital
- Endpoint REST documentado
- Autenticação: Certificado A1/A3

### Fase 3: Automatização (Semanas 11-16)
**Tecnologia:** Sync automático + Notificações

#### Sync Automático:
```bash
# Cron job - roda diariamente 3h da manhã
0 3 * * * python scripts/sync_jurisprudencia.py --source=all
```

#### Fluxo de Dados:
```
Scraper → Normalização → Banco → Notificação
                ↓
        Extrair Prazos → Criar Deadline
                ↓
        Notificar WhatsApp/Email
```

### Ordem de Implementação:
1. **STJ** (Semanas 1-3) - Mais fácil, API amigável
2. **STF** (Semanas 3-5) - Volume menor, mais estável
3. **TJSP** (Semanas 5-9) - Mais complexo, maior volume
4. **TRF-3** (Semanas 9-11) - API certificado
5. **Outros TRFs** (Semanas 11-14)
6. **Outros TJs** (Semanas 14-20)

### Custo Operacional:
- VPS Scraping: R$ 200/mês
- Storage: R$ 150/mês (crescendo)
- Desenvolvimento: 4-6 meses

---

## ROADMAP CONSOLIDADO (Próximos 6 meses)

### Mês 1: Fundação
- Semana 1-2: Segurança (PostgreSQL, backup, testes)
- Semana 3-4: Início Módulo 2 (Gestão de Equipe)

### Mês 2: Equipe + Portal
- Semana 5-6: Finalizar Gestão de Equipe
- Semana 7-8: Portal do Cliente

### Mês 3: Atendimento + Marketing
- Semana 9-10: Fila de Atendimento Inteligente
- Semana 11-12: Marketing OAB-Compliance

### Mês 4: Jurisprudência Fase 1
- Semana 13-14: STJ + STF integração
- Semana 15-16: Frontend Jurisprudência

### Mês 5: Jurisprudência Fase 2
- Semana 17-18: TJSP + TRF-3
- Semana 19-20: IA Análise de Tendências

### Mês 6: Polimento + Lançamento
- Semana 21-22: Testes, documentação
- Semana 23-24: Performance tuning
- Go-live versão 2.0

---

## ESTIMATIVA DE INVESTIMENTO

### Desenvolvimento (6 meses):
- 3 devs backend senior: R$ 25.000/mês × 6 = R$ 150.000
- 2 devs frontend: R$ 18.000/mês × 6 = R$ 108.000
- 1 devops: R$ 20.000/mês × 6 = R$ 120.000
- **Total desenvolvimento: R$ 378.000**

### Infraestrutura (mensal):
- Servidores (AWS/GCP): R$ 2.000
- Banco de dados: R$ 500
- Storage/S3: R$ 300
- APIs externas (Groq, Twilio): R$ 1.500
- **Total mensal: R$ 4.300**

### Total para Go-live:
- **6 meses desenvolvimento: R$ 378.000**
- **6 meses infra: R$ 25.800**
- **Grand Total: R$ 403.800**

---

## PRÓXIMOS PASSOS

1. **Aprovar especificações** (este documento)
2. **Revisar cronograma** com time técnico
3. **Ajustar orçamento** se necessário
4. **Iniciar Fase 1** (Segurança + PostgreSQL)

---

**Documentos detalhados por módulo:**
- `MODULO_1_JURISPRUDENCIA_DETALHADO.md`
- `MODULO_2_GESTAO_EQUIPE_DETALHADO.md`  
- `MODULO_3_FILA_ATENDIMENTO_DETALHADO.md`
- `MODULO_4_MARKETING_OAB_DETALHADO.md`
- `PORTAL_CLIENTE_DETALHADO.md`
- `INTEGRACAO_TRIBUNAIS_DETALHADO.md`

