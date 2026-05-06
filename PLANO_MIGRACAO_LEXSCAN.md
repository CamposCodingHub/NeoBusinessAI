# 📋 Plano de Migração: NeoBusiness AI → LexScan IA

## 🎯 Objetivo
Transformar o projeto de "assistente de negócios genérico" para "automação documental jurídica com OCR + IA"

---

## 📁 Estrutura Atual → Nova

### Backend
```
ai/
├── engine.py          → LexScanEngine (processamento de documentos)
├── brain.py           → DocumentClassifier (classificação de docs)
├── memory.py          → SessionManager (sessões de upload)
├── vector_store.py    → DocumentStore (vetores de documentos)
├── groq_client.py     → LLMClient (mantém)
└── prompts.py         → LegalPrompts (prompts jurídicos)

tools/
├── web_search.py      → OCRProcessor (Tesseract/EasyOCR)
├── document_parser.py → NOVO (extrai texto de PDFs/imagens)
├── deadline_extractor → NOVO (extrai prazos processuais)
└── notification.py    → NOVO (sistema de alertas)

models/
├── document.py        → NOVO (modelo de documento)
├── user.py            → NOVO (modelo de usuário/escritório)
└── deadline.py        → NOVO (modelo de prazo)

main.py                → FastAPI com endpoints de upload/análise
```

### Frontend
```
app/
├── chat/page.tsx      → dashboard/page.tsx (painel de documentos)
├── upload/            → NOVO (página de upload)
├── documents/         → NOVO (lista de documentos)
├── deadlines/         → NOVO (calendário de prazos)
└── settings/          → NOVO (configurações)

components/
├── DocumentUpload.tsx → NOVO (drag & drop)
├── DocumentViewer.tsx → NOVO (visualizador com OCR)
├── DeadlineCard.tsx   → NOVO (card de prazo)
├── SummaryPanel.tsx   → NOVO (painel de resumo)
└── ChatLegal.tsx      → NOVO (chat contextual jurídico)
```

---

## 🛠️ Fases de Implementação

### FASE 1 - MVP Básico (2-3 dias)
- [x] 1.1 Renomear projeto e branding
- [ ] 1.2 Criar sistema de upload de documentos
- [ ] 1.3 Integrar OCR (Tesseract)
- [ ] 1.4 Extrair texto de PDFs
- [ ] 1.5 Dashboard básico

### FASE 2 - IA e Resumos (2-3 dias)
- [ ] 2.1 Prompts jurídicos otimizados
- [ ] 2.2 Geração de resumos automáticos
- [ ] 2.3 Extração de dados-chave (partes, valores, datas)
- [ ] 2.4 Chat contextual com documento

### FASE 3 - Prazos e Alertas (2-3 dias)
- [ ] 3.1 Detecção de prazos processuais
- [ ] 3.2 Calendário de prazos
- [ ] 3.3 Sistema de notificações
- [ ] 3.4 Alertas por email/SMS

### FASE 4 - UX e refinamento (2-3 dias)
- [ ] 4.1 Interface tipo "Legal Tech"
- [ ] 4.2 Visualizador de documentos
- [ ] 4.3 Marcação de texto relevante
- [ ] 4.4 Exportação de relatórios

---

## 🎨 Identidade Visual LexScan

### Cores
- **Primária:** Azul escuro (#1e3a5f) - confiança, seriedade jurídica
- **Secundária:** Dourado (#c9a227) - excelência, premium
- **Destaque:** Verde (#10b981) - sucesso, aprovação
- **Alerta:** Vermelho (#ef4444) - prazos críticos

### Tipografia
- **Títulos:** Inter ou Playfair Display (serifada para elegância jurídica)
- **Corpo:** Inter ou Roboto (legibilidade)

### Tom de Voz
- **Formal mas acessível**
- **Preciso e confiável**
- **Orientado a resultados**

---

## 💰 Modelo SaaS a Implementar

### Planos
```
STARTER (R$ 297/mês)
- 50 documentos/mês
- OCR básico
- Resumo automático
- 1 usuário
- Suporte por email

PROFESSIONAL (R$ 897/mês) ⭐ POPULAR
- 200 documentos/mês
- OCR avançado + IA
- Detecção de prazos
- Chat contextual
- 5 usuários
- API básica
- Suporte prioritário

BUSINESS (R$ 2.500/mês)
- Documentos ilimitados
- IA treinável personalizada
- White-label
- Integrações ERP
- 20 usuários
- API completa
- Consultoria incluída
- SLA garantido

ENTERPRISE (Sob consulta)
- Infraestrutura dedicada
- IA customizada
- Integrações enterprise
- Usuários ilimitados
- Suporte 24/7
- Auditoria e compliance
```

---

## 🔐 Segurança e Compliance

- [ ] Criptografia AES-256
- [ ] LGPD compliance
- [ ] Backup automático
- [ ] Logs de auditoria
- [ ] Autenticação 2FA
- [ ] Assinatura digital (DocuSign integração)

---

## 📊 Métricas de Sucesso (KPIs)

- **Tempo médio** de processamento de documento
- **Taxa de precisão** do OCR
- **Documentos processados** por mês
- **Prazos detectados** corretamente
- **NPS** dos clientes
- **Churn rate** mensal
- **MRR** (Monthly Recurring Revenue)

---

## 🚀 Próximos Passos Imediatos

1. **Renomear branding** (hoje)
2. **Criar nova landing page** (hoje)
3. **Sistema de upload** (amanhã)
4. **Integrar OCR** (amanhã)
5. **Dashboard v1** (depois de amanhã)

**Total estimado: 10-14 dias para MVP funcional**

---

## ⚡ Vantagens de Usar NeoBusiness como Base

✅ Backend FastAPI já pronto
✅ Integração com Groq API (rápida)
✅ Frontend Next.js funcionando
✅ Autenticação Firebase OK
✅ Deploy pipeline pronto

**Economia de tempo: ~60% do trabalho já está feito!**

---

## 🎯 Decisão

**Recomendo fortemente fazer a migração porque:**

1. **LexScan tem mercado definido** (advocacia) vs NeoBusiness (genérico)
2. **Dor específica** (prazos documentais) vs "ajuda de negócios"
3. **Modelo SaaS mais claro** - recorrência jurídica é estável
4. **Menos concorrência** direta no nicho jurídico específico
5. **Valor percebido alto** - advogados pagam bem por produtividade

---

## ✅ Aprovação para Começar?

Quer que eu **comece agora** a transformar o projeto?

Posso começar por:
1. Renomear tudo para LexScan
2. Criar nova landing page jurídica
3. Sistema de upload de documentos
4. Ou outra prioridade que você definir

**Estou pronto quando você estiver!** 🚀
