# 🧠 Como a NeoBusiness AI Busca Informações

## 📊 Fontes de Conhecimento (Ordem de Uso)

```
┌─────────────────────────────────────────────────────────────┐
│                    PERGUNTA DO USUÁRIO                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 1️⃣  MEMÓRIA DA CONVERSA                                    │
│    └─> Contexto das últimas 3 mensagens                     │
│    └─> "O usuário perguntou X antes, agora quer Y"         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2️⃣  RAG - SEUS DOCUMENTOS (PDFs)                          │
│    └─> Busca nos PDFs que você enviou                       │
│    └─> Procedimentos, manuais, documentos da empresa        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3️⃣  MODELO LLM (Llama 3.1 via Groq API)                    │
│    └─> Conhecimento geral do mundo (até 2023)               │
│    └─> Estratégias de negócio, marketing, vendas            │
│    └─> NÃO tem acesso à internet em tempo real              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4️⃣  WEB SEARCH (Opcional - quando ativado)                 │
│    └─> Busca no Google/DuckDuckGo                           │
│    └─> Preços, notícias, informações atualizadas            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detalhamento de Cada Fonte

### 1. 📚 Memória da Conversa (CURTO PRAZO)
**O que é:** Lembra do que vocês já conversaram

**Exemplo:**
```
Usuário: "Meu nome é João"
... 3 mensagens depois...
Usuário: "Qual meu nome?"
IA: "Seu nome é João!" ✅ (lembrou da memória)
```

**Limite:** Últimas 3 interações apenas (para não ficar lento)

---

### 2. 📄 RAG - Seus PDFs (CONHECIMENTO ESPECÍFICO)
**O que é:** Documentos que VOCÊ enviou para a pasta `backend/pdfs/`

**Exemplos:**
- Manual da sua empresa
- Procedimentos internos
- Catálogo de produtos
- Políticas de RH
- Documentos técnicos

**Como funciona:**
1. PDFs são convertidos em texto
2. Texto é dividido em "pedacinhos"
3. Quando você pergunta, busca os pedaços relevantes
4. IA responde baseada NOS SEUS documentos

**Exemplo prático:**
```
PDF: "Manual de Vendas da Empresa XYZ"
      └─> "Política de desconto máximo: 15%"

Usuário: "Qual o desconto máximo?"
IA: "Segundo o manual da empresa, o desconto máximo é 15%" ✅
```

---

### 3. 🧠 Modelo LLM - Llama 3.1 (CONHECIMENTO GERAL)
**O que é:** Cérebro treinado com bilhões de textos da internet

**Conhecimento que ela TEM:**
- ✅ Estratégias de marketing e vendas
- ✅ Conceitos de negócio (ROI, CAC, LTV)
- ✅ Gestão empresarial
- ✅ Como criar planos de negócio
- ✅ Técnicas de atendimento
- ✅ Conhecimento até ~2023

**Conhecimento que ela NÃO TEM:**
- ❌ Preços atuais de produtos
- ❌ Notícias de hoje
- ❌ Dados específicos da SUA empresa (sem PDFs)
- ❌ Clima de agora
- ❌ Cotação do dólar agora

**Analogia:** É como um consultor experiente que leu milhares de livros de negócios, mas não tem acesso à internet.

---

### 4. 🌐 Web Search (INTERNET - OPCIONAL)
**O que é:** Busca no Google quando necessário

**Quando ativa:**
- Você pergunta sobre "preço de X"
- Você pergunta "últimas notícias"
- Você quer dados atualizados

**Como funciona:**
```
Usuário: "Quanto custa um iPhone 15?"
IA: "Deixa eu buscar para você..."
[Busca no Google]
IA: "O iPhone 15 está custando R$ 7.999 no site da Apple" ✅
```

**Status atual:** Desativado por padrão (pode ativar no código)

---

## 🎯 Resumo Visual

| Fonte | Tipo de Info | Tempo Real? | Você Controla? |
|-------|--------------|-------------|----------------|
| **Memória** | Contexto conversa | ✅ Sim | ❌ Automático |
| **PDFs** | Docs da empresa | ✅ Sim | ✅ Adicione PDFs |
| **LLM** | Conhecimento geral | ❌ Até 2023 | ❌ Pré-treinado |
| **Web** | Internet | ✅ Sim | ⚠️ Pode ativar |

---

## 💡 Como Melhorar as Respostas

### Quer respostas mais precisas sobre SUA empresa?
**Solução:** Adicione PDFs na pasta `backend/pdfs/`

1. Coloque PDFs na pasta
2. Reinicie o servidor
3. A IA vai responder baseada nos seus documentos!

### Quer dados atualizados (preços, notícias)?
**Solução:** Ativar Web Search

### Quer respostas mais inteligentes?
**Já está ativo!** Usando Groq API com Llama 3.1 (um dos melhores modelos)

---

## ⚠️ Limitações Atuais

1. **Sem acesso ao seu banco de dados** (vendas, clientes, estoque)
2. **Sem acesso a sistemas internos** (ERP, CRM)
3. **Conhecimento geral até 2023** (não sabe de eventos recentes)
4. **Não aprende permanentemente** (reinicia a memória a cada sessão)

---

## 🚀 Possibilidades Futuras

Queremos adicionar:
- ✅ Integração com seu banco de dados
- ✅ Acesso a planilhas (Google Sheets, Excel)
- ✅ Conexão com APIs da sua empresa
- ✅ Web search sempre ativo
- ✅ Aprendizado contínuo

---

## ❓ Exemplo Comparativo

**Pergunta:** "Como aumentar vendas?"

| Fonte | Tipo de Resposta |
|-------|------------------|
| **Só LLM** | Estratégias gerais de marketing (funil, SEO, redes sociais) |
| **LLM + PDFs** | Estratégias + procedimentos específicos da SUA empresa |
| **LLM + PDFs + Web** | Estratégias + seus docs + tendências atuais de mercado |

---

**Resumo:** A NeoBusiness AI é como um consultor experiente que:
- 📚 Leu milhares de livros de negócios
- 📄 Pode ler seus documentos (se você der)
- 💬 Lembra o que vocês conversaram
- 🌐 Pode buscar na internet (se ativar)
