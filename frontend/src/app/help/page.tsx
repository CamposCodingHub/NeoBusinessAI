"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";

const colors = {
  primary: "#1e3a5f",
  secondary: "#c9a227",
  accent: "#10b981",
  danger: "#ef4444",
  dark: "#0f172a",
  light: "#f8fafc",
  gray: "#64748b"
};

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
}

const faqData: FAQItem[] = [
  // Categoria: Começando
  {
    id: "what-is-lexscan",
    category: "Começando",
    question: "O que é o LexScan IA?",
    answer: `LexScan IA é uma plataforma de automação documental jurídica que utiliza Inteligência Artificial e OCR (Reconhecimento Óptico de Caracteres) para processar documentos jurídicos.

Com o LexScan você pode:
• 📄 Extrair texto automaticamente de PDFs e imagens
• 🤖 Analisar documentos com IA
• ⏰ Detectar prazos processuais automaticamente
• 💬 Conversar com seus documentos
• 📊 Gerar relatórios PDF
• 🔔 Receber alertas de prazos por email

Tudo em uma interface simples e profissional, desenvolvida especificamente para advogados e escritórios jurídicos.`
  },
  {
    id: "how-to-start",
    category: "Começando",
    question: "Como começar a usar o LexScan IA?",
    answer: `Siga estes passos simples:

1. **Crie sua conta**
   - Clique em "Começar Agora" na landing page
   - Faça login com Google ou email

2. **Upload do primeiro documento**
   - No Dashboard, vá para a aba "Upload"
   - Arraste um PDF ou clique para selecionar
   - Aguarde o processamento (geralmente 3-5 segundos)

3. **Explore seu documento**
   - Veja o resumo automático
   - Confira os prazos detectados
   - Converse com o documento no chat

4. **Acompanhe prazos**
   - Use a aba "Calendário" para visualizar todos os prazos
   - Receba alertas automáticos por email

5. **Exporte relatórios**
   - Gere PDFs profissionais para seus clientes

**Dica:** Comece com o plano gratuito (5 documentos) para testar todas as funcionalidades!`
  },
  {
    id: "free-plan",
    category: "Começando",
    question: "O que está incluído no plano gratuito?",
    answer: `O plano gratuito inclui:

✅ **5 documentos** para processar
✅ **OCR completo** (extrai texto de PDFs e imagens)
✅ **Análise de IA** (resumos e identificação de dados)
✅ **Detecção de prazos** automática
✅ **Calendário visual** de prazos
✅ **Chat com documentos**
✅ **Exportação de PDFs**
✅ **Suporte por email**

**Limitações do plano gratuito:**
• Limite de 5 documentos no total
• 1 usuário apenas
• Sem notificações automáticas por email
• Sem API de integração

Quando atingir o limite de 5 documentos, você pode fazer upgrade para um plano pago a qualquer momento!`
  },

  // Categoria: OCR e Documentos
  {
    id: "supported-formats",
    category: "OCR e Documentos",
    question: "Quais formatos de arquivo são suportados?",
    answer: `O LexScan IA suporta os seguintes formatos:

**📄 PDFs**
• PDFs digitais (com texto selecionável)
• PDFs escaneados (imagens)
• PDFs mistos (páginas com texto e imagens)
• PDFs digitais com até 500 páginas
• PDFs escaneados com até 100 páginas de OCR

**🖼️ Imagens**
• JPG/JPEG
• PNG
• TIFF

**Documentos editáveis**
• DOCX
• TXT
• RTF

**⚠️ Limitações:**
• Tamanho máximo: **50 MB** por arquivo
• O formato DOC legado deve ser convertido para DOCX ou PDF
• Resolução mínima recomendada: **200 DPI**
• Idiomas suportados: **Português** (principal), Inglês e Espanhol

**Dica para melhores resultados:**
• Use PDFs de boa qualidade
• Evite documentos muito escuros ou desfocados
• Para documentos manuscritos, a precisão pode variar`
  },
  {
    id: "ocr-accuracy",
    category: "OCR e Documentos",
    question: "Qual a precisão do OCR?",
    answer: `A precisão do OCR depende da qualidade do documento:

**📊 Estatísticas médias:**
• PDFs digitais (texto selecionável): **98-99%**
• PDFs escaneados (alta qualidade): **85-95%**
• PDFs escaneados (baixa qualidade): **70-85%**
• Imagens de celular (boa iluminação): **80-90%**

**Fatores que afetam a precisão:**
✅ **Melhoram OCR:**
• Alta resolução (300+ DPI)
• Boa iluminação
• Texto nítido
• Fontes padrão

❌ **Prejudicam OCR:**
• Baixa resolução
• Documentos amassados
• Texto manuscrito
• Fundos coloridos/padrões
• Fontes muito decorativas

**O que fazer se o OCR falhar?**
• Você pode inserir o texto manualmente
• Sistema aceita upload de texto puro
• Nossa IA ainda processa o conteúdo manual`
  },
  {
    id: "processing-time",
    category: "OCR e Documentos",
    question: "Quanto tempo leva para processar um documento?",
    answer: `O tempo de processamento depende do tipo e tamanho do documento:

**⏱️ Tempos médios:**
• PDF digital (1-5 páginas): **2-4 segundos**
• PDF escaneado (1-5 páginas): **5-10 segundos**
• PDF grande (20+ páginas): **15-30 segundos**
• Imagem única: **3-6 segundos**

**O que acontece durante o processamento?**
1. **Upload** do arquivo (1-2s)
2. **Fila segura** - O documento aguarda um worker disponível
3. **OCR** - Extração de texto e estrutura
4. **Análise profissional** - Riscos, prazos, valores, partes e obrigações
5. **Consolidação** - Resultado e trilha técnica são gravados

Arquivos extensos continuam em segundo plano. Você pode navegar pelo sistema e
retornar depois sem perder o progresso.

**Durante o processamento você verá:**
• Barra de progresso e etapa atual
• Estados "Na fila", "Processando", "Concluído" ou "Requer atenção"
• Botão de nova tentativa quando a análise falhar
• Resultado completo com resumo, análise, partes, prazos e valores

Se um documento demorar mais de 60 segundos, entre em contato com o suporte.`
  },

  // Categoria: Prazos e Alertas
  {
    id: "how-deadlines-work",
    category: "Prazos e Alertas",
    question: "Como funciona a detecção automática de prazos?",
    answer: `Nossa IA identifica prazos processuais automaticamente:

**🔍 O que detectamos:**
• "Prazo para contestação: 15 dias"
• "Prazo em 30 dias para recurso"
• "Em 05 dias úteis"
• "Prazo legal de 48 horas"
• "Intimação para comparecimento em 10 dias"

**🎯 Sistema de urgência:**
• **🔴 URGENTE:** Até 15 dias
• **🟠 MÉDIO:** 16-30 dias
• **🟢 BAIXO:** Mais de 30 dias

**📍 Onde você encontra os prazos:**
1. **Dashboard** - Lista resumida
2. **Aba "Prazos"** - Lista completa com filtros
3. **Aba "Calendário"** - Visualização mensal
4. **No documento** - Seção específica

**⚡ Alertas automáticos:**
• Emails diários com prazos do dia
• Notificação 3 dias antes de prazos urgentes
• Resumo semanal de todos os prazos

**Dica:** Você pode marcar prazos como "Concluídos" quando cumprir!`
  },
  {
    id: "email-notifications",
    category: "Prazos e Alertas",
    question: "Como configurar notificações por email?",
    answer: `Para receber alertas de prazos por email:

**1. Configuração inicial:**
• Vá em **Configurações > Notificações**
• Adicione seu email principal
• Clique em "Testar envio" para verificar

**2. Tipos de notificações:**
• **Diário:** Prazos do dia (7h da manhã)
• **Semanal:** Resumo de todos os prazos (segunda-feira)
• **Urgente:** Alerta 3 dias antes de prazos 🔴
• **Imediato:** Novo documento processado

**3. Fusos horários:**
• Selecione seu fuso horário nas configurações
• Padrão: Brasília (UTC-3)

**⚠️ Importante:**
• Verifique a caixa de spam nas primeiras notificações
• Adicione "noreply@lexscan.ai" aos contatos
• Você pode desativar a qualquer momento

**Problemas comuns:**
❓ Não recebendo emails?
→ Verifique a pasta de spam
→ Confirme se o email está correto
→ Teste o envio nas configurações`
  },
  {
    id: "calendar-view",
    category: "Prazos e Alertas",
    question: "Como usar o calendário de prazos?",
    answer: `O calendário visual é uma das ferramentas mais poderosas do LexScan:

**📅 Visualização:**
• Grade mensal (domingo a sábado)
• Navegação fácil entre meses
• Hoje destacado automaticamente
• Dias com prazos marcados com 🔴🟠🟢

**🎨 Cores dos prazos:**
• **Vermelho:** Prazo URGENTE (até 15 dias)
• **Amarelo/Laranja:** Prazo MÉDIO (16-30 dias)
• **Verde:** Prazo BAIXO (mais de 30 dias)

**👆 Interações:**
• **Clique no dia:** Abre modal com todos os prazos daquele dia
• **Clique em prazo:** Vai direto para o documento
• **Navegação:** Setas para mês anterior/próximo
• **Hoje:** Botão para voltar ao mês atual

**💡 Dicas:**
• Use o calendário para planejar sua semana
• Identifique visualmente dias com múltiplos prazos
• Combine com a lista de prazos para detalhes

**📱 Mobile:**
O calendário é totalmente responsivo e funciona perfeitamente no celular!`
  },

  // Categoria: Chat e IA
  {
    id: "chat-how-it-works",
    category: "Chat e IA",
    question: "Como funciona o Chat com Documento?",
    answer: `O Chat Contextual é como ter um assistente jurídico disponível 24/7:

**💬 O que você pode perguntar:**

**Sobre Partes:**
• "Quem é o autor da ação?"
• "Qual o nome do réu?"
• "Quem é o advogado?"

**Sobre Valores:**
• "Qual o valor da causa?"
• "Quanto o autor está pedindo?"
• "Quais os honorários advocatícios?"

**Sobre Prazos:**
• "Qual o prazo para contestar?"
• "Quando vence o prazo de recurso?"
• "Quantos dias restantes?"

**Sobre Conteúdo:**
• "Resuma o caso em 3 linhas"
• "Quais são os argumentos principais?"
• "O que o autor está pedindo?"
• "Quais provas foram juntadas?"

**Sobre Processo:**
• "Qual o número do processo?"
• "Em qual vara tramita?"
• "Existe contestação?"

**🤖 Como funciona:**
1. A IA lê todo o documento processado
2. Extrai informações relevantes
3. Responde baseada apenas no documento
4. Fornece respostas precisas e objetivas

**⚡ Respostas instantâneas:**
• Tempo médio: 1-2 segundos
• Disponível 24/7
• Sem limites de perguntas`
  },
  {
    id: "chat-general",
    category: "Chat e IA",
    question: "Posso conversar sobre assuntos gerais (sem documento)?",
    answer: `Sim! Temos dois modos de chat:

**1. Chat com Documento (Contextual)**
• Perguntas sobre um documento específico
• Respostas baseadas no conteúdo do documento
• Acesso via Dashboard > Clique em "Chat" no documento

**2. Chat Geral (Assistente Jurídico)**
• Perguntas sobre qualquer assunto jurídico
• Dúvidas sobre direito
• Explicações de conceitos
• Ajuda com o sistema LexScan

**Exemplos de perguntas gerais:**
• "O que é rescisão indireta?"
• "Explique o princípio da inércia tributária"
• "Como funciona o sistema de prazos no LexScan?"
• "Qual a diferença entre ação declaratória e constitutiva?"
• "O que significa 'in dubio pro reo'?"

**🎓 Conhecimento da IA:**
• Direito Constitucional
• Direito Civil
• Direito Processual Civil
• Direito Trabalhista
• Direito Penal (básico)
• Direito Tributário (básico)

**⚠️ Limitações:**
• Não substitui um advogado
• Não fornece consultoria personalizada
• Baseado em conhecimento geral, não em legislação atualizada em tempo real`
  },
  {
    id: "ai-accuracy",
    category: "Chat e IA",
    question: "Qual a precisão da IA? Posso confiar nas respostas?",
    answer: `A precisão varia conforme o tipo de pergunta:

**📊 Taxas de acerto:**

**Extração de Dados (Chat com Documento):**
• Nomes de partes: **95%**
• Valores monetários: **90%**
• Números de processo: **98%**
• Prazos: **92%**
• Datas: **88%**

**Respostas Gerais:**
• Conceitos jurídicos: **85-90%**
• Explicações de direito: **80-85%**
• Dúvidas sobre o sistema: **95%**

**⚠️ Sempre verifique:**
• Valores importantes (causa, condenação)
• Nomes de partes (para petições)
• Prazos processuais (dobro do prazo em dobro, etc.)
• Datas cruciais

**✅ Use como:**
• Primeira análise rápida
• Auxiliar na compreensão
• Organização de informações
• Esqueleto de trabalho

**❌ Não use como:**
• Única fonte para decisões importantes
• Substituto de análise humana
• Consultoria jurídica personalizada
• Base para petições sem revisão

**🎯 Melhor prática:**
Trate as respostas da IA como um "primeiro rascunho" que deve ser revisado por um profissional.`
  },

  // Categoria: Planos e Pagamentos
  {
    id: "plans-comparison",
    category: "Planos e Pagamentos",
    question: "Qual plano é ideal para mim?",
    answer: `Escolha baseado no volume de trabalho:

**🆓 PLANO GRATUITO (R$ 0)**
• **Ideal para:** Testar a plataforma
• **Inclui:** 5 documentos, OCR, análise básica
• **Não inclui:** Notificações email, múltiplos usuários

**💼 STARTER (R$ 297/mês)**
• **Ideal para:** Advogados autônomos
• **Inclui:** 50 documentos/mês, 1 usuário
• **Recursos:** OCR, resumos, chat, suporte email
• **Melhor para:** 1-2 processos por semana

**⭐ PROFESSIONAL (R$ 897/mês)** ⭐ POPULAR
• **Ideal para:** Escritórios pequenos
• **Inclui:** 200 documentos/mês, 5 usuários
• **Recursos:** OCR avançado, detecção de prazos, chat contextual, API básica
• **Melhor para:** 5-10 processos por semana, equipe de 2-5 pessoas

**🏢 BUSINESS (R$ 2.500/mês)**
• **Ideal para:** Escritórios médios
• **Inclui:** Documentos ilimitados, 20 usuários
• **Recursos:** IA personalizada, white-label, integrações ERP, consultoria
• **Melhor para:** Escritórios com alto volume, integração com sistemas

**🏛️ ENTERPRISE (Sob consulta)**
• **Ideal para:** Grandes escritórios, departamentos jurídicos de empresas
• **Inclui:** Tudo ilimitado + infraestrutura dedicada
• **Recursos:** Personalização total, suporte 24/7, SLA garantido
• **Melhor para:** Grandes volumes, necessidades específicas

**📞 Não tem certeza?**
Comece com o **Gratuito** e faça upgrade quando atingir o limite!`
  },
  {
    id: "payment-methods",
    category: "Planos e Pagamentos",
    question: "Quais formas de pagamento são aceitas?",
    answer: `Aceitamos diversas formas de pagamento:

**💳 Cartões de Crédito:**
• Visa
• Mastercard
• American Express
• Hipercard
• Elo

**💳 Cartões de Débito:**
• Visa Electron
• Maestro

**📱 Outras formas:**
• PIX (processado via Stripe)
• Boleto bancário (para planos anuais)

**💰 Faturamento:**
• Mensal (paga todo mês)
• Anual (10% de desconto)

**🛡️ Segurança:**
• Processado via **Stripe** (PCI DSS compliant)
• Seus dados de cartão **nunca** são armazenados em nossos servidores
• Conexão SSL 256-bit

**📄 Nota Fiscal:**
• NF-e emitida automaticamente
• Enviada para email cadastrado
• Disponível no painel de controle

**❓ Problemas com pagamento?**
• Verifique limite do cartão
• Confirme dados do cartão
• Tente outro cartão
• Entre em contato: financeiro@lexscan.ai`
  },
  {
    id: "change-plan",
    category: "Planos e Pagamentos",
    question: "Posso trocar de plano ou cancelar?",
    answer: `Sim! Você tem total flexibilidade:

**🔄 Fazer Upgrade (aumentar plano):**
• Pode ser feito a qualquer momento
• Cobrança proporcional ao dia
• Acesso imediato aos novos recursos
• Documentos anteriores mantidos

**⬇️ Fazer Downgrade (diminuir plano):**
• Pode ser feito a qualquer momento
• Mudança efetiva no próximo ciclo de faturamento
• Se exceder novo limite, precisa remover documentos

**❌ Cancelar assinatura:**
• Sem multa ou taxa de cancelamento
• Acesso mantido até o fim do período pago
• Exporte seus dados antes de cancelar
• Reembolso proporcional em até 7 dias (garantia)

**📅 Ciclo de faturamento:**
• Baseado na data da assinatura
• Exemplo: Assinou dia 15, próxima cobrança dia 15
• Lembretes 3 dias antes da renovação

**⚠️ Ao cancelar:**
• Seus documentos ficam disponíveis por 30 dias
• Após 30 dias, dados são arquivados (não deletados)
• Pode reativar a qualquer momento
• Planos gratuitos mantêm acesso limitado

**💡 Dica:**
Use o período de teste gratuito (5 documentos) para avaliar antes de comprar!`
  },

  // Categoria: Relatórios e Exportação
  {
    id: "pdf-reports",
    category: "Relatórios e Exportação",
    question: "Como funcionam os relatórios em PDF?",
    answer: `Gere relatórios profissionais em segundos:

**📄 Tipos de relatórios:**

**1. Relatório de Documento Individual**
• Informações completas do documento
• Partes do processo
• Prazos identificados
• Análise e resumo
• Ideal para: Anexar a processos, enviar a clientes

**2. Relatório de Dashboard Geral**
• Estatísticas do escritório
• Todos os documentos processados
• Prazos urgentes destacados
• Resumo mensal
• Ideal para: Reuniões de equipe, relatórios gerenciais

**🎨 Formatação:**
• Cabeçalho com branding LexScan IA
• Tabelas profissionais
• Cores corporativas
• Numeração de páginas
• Data de geração

**💾 Como exportar:**
1. No documento: Clique em "Exportar PDF"
2. No dashboard: Clique em "Relatório Geral"
3. Download automático
4. Nome do arquivo: relatorio_[nome]_[data].pdf

**📊 Dados incluídos:**
• Tipo de documento
• Número do processo
• Partes (autor, réu, advogados)
• Prazos com urgência colorida
• Valores identificados
• Resumo executivo
• Análise detalhada

**🔒 Segurança:**
• PDFs não são armazenados em nuvem
• Download direto para seu dispositivo
• Sem watermark`
  },

  // Categoria: Segurança e Privacidade
  {
    id: "data-security",
    category: "Segurança e Privacidade",
    question: "Meus documentos estão seguros?",
    answer: `Sim! Segurança é nossa prioridade:

**🔐 Criptografia:**
• **Em trânsito:** TLS 1.3 (HTTPS)
• **Em repouso:** AES-256
• **Banco de dados:** Encriptação de colunas sensíveis

**🛡️ Infraestrutura:**
• Servidores na **AWS** / **Google Cloud**
• Certificação **ISO 27001**
• Firewall e DDoS protection
• Monitoramento 24/7

**👤 Privacidade (LGPD):**
• Você mantém **direito autoral** sobre seus documentos
• Não usamos seus dados para treinar IA
• Não compartilhamos com terceiros
• Exclusão permanente sob demanda

**📋 Acesso:**
• Apenas você acessa seus documentos
• Autenticação via Firebase (Google)
• Controle de acesso por usuário (planos multi-user)
• Logs de acesso disponíveis

**🗑️ Retenção de dados:**
• Documentos mantidos enquanto conta ativa
• Backup automático por 30 dias
• Após exclusão, dados removidos em até 90 dias

**⚖️ Compliance:**
• Conformidade com **LGPD** (Lei 13.709/2018)
• Termos de Uso claros
• Política de Privacidade detalhada
• DPO (Data Protection Officer): dpo@lexscan.ai

**🔍 Auditoria:**
• Logs de todas as operações
• Rastreabilidade completa
• Relatórios de acesso disponíveis

**💡 Dica:**
Para documentos ultra-sensíveis, use criptografia adicional antes do upload (PGP).`
  },
  {
    id: "delete-account",
    category: "Segurança e Privacidade",
    question: "Como excluir minha conta e dados?",
    answer: `Você pode solicitar exclusão a qualquer momento:

**🗑️ Para excluir sua conta:**

1. **Exporte seus dados** (recomendado)
   - Relatórios PDF dos documentos importantes
   - Dados do dashboard

2. **Acesse Configurações**
   - Clique no avatar (canto superior direito)
   - "Configurações da Conta"
   - "Privacidade e Dados"

3. **Solicite exclusão**
   - "Excluir minha conta"
   - Confirme com senha
   - Escolha tipo de exclusão:

**📦 Opções de exclusão:**

• **Soft Delete (Padrão):**
  - Dados inativados por 30 dias
  - Pode recuperar durante esse período
  - Após 30 dias, exclusão permanente

• **Hard Delete (Imediato):**
  - Exclusão permanente imediata
  - Não pode ser desfeita
  - Todos os dados removidos

**⏱️ Prazos:**
• Soft Delete: 30 dias para recuperação
• Hard Delete: Processamento em até 7 dias úteis
• Confirmação por email quando concluído

**📧 Contato direto:**
Envie email para **dpo@lexscan.ai** com assunto "Solicitação de Exclusão LGPD"

**⚠️ Importante:**
• Documentos em processo judicial devem ser preservados
• Backup de segurança pode reter dados por até 90 dias
• Dados anonimizados podem ser mantidos para estatísticas`
  },

  // Categoria: Solução de Problemas
  {
    id: "upload-fails",
    category: "Solução de Problemas",
    question: "O upload falhou. O que fazer?",
    answer: `Solução de problemas comuns de upload:

**❌ Erro: "Arquivo muito grande"**
• Limite: 50 MB
• Solução: Compacte o PDF ou divida em partes

**❌ Erro: "Formato não suportado"**
• Verifique extensão: .pdf, .jpg, .png
• Solução: Converta para PDF

**❌ Erro: "OCR falhou"**
• PDF pode estar protegido por senha
• Qualidade muito baixa
• Solução: Remova proteção ou use texto manual

**❌ Erro: "Limite de documentos atingido"**
• Plano gratuito: 5 documentos
• Solução: Faça upgrade ou delete documentos antigos

**❌ Erro: "Erro de rede"**
• Verifique conexão com internet
• Tente novamente em alguns segundos
• Use cabo de rede em vez de WiFi (se possível)

**🔧 Passos de diagnóstico:**

1. **Verifique o arquivo**
   ~~~
   • Abre normalmente no visualizador de PDF?
   • Não está corrompido?
   • Tem mais de 0 bytes?
   ~~~

2. **Teste com outro arquivo**
   ~~~
   • Tente um PDF simples de 1 página
   • Se funcionar, problema é específico do arquivo
   ~~~

3. **Verifique tamanho**
   ~~~
   • Clique direito > Propriedades
   • Deve ser menor que 50 MB
   ~~~

4. **Tente navegador diferente**
   ~~~
   • Chrome, Firefox, Safari, Edge
   • Desative extensões (AdBlock, etc.)
   ~~~

**📞 Se nada funcionar:**
Envie o arquivo para **suporte@lexscan.ai** com descrição do erro.`
  },
  {
    id: "ocr-poor-quality",
    category: "Solução de Problemas",
    question: "O OCR extraiu texto com muitos erros. Como melhorar?",
    answer: `Melhore a qualidade do OCR:

**📷 Para PDFs escaneados:**

1. **Melhore a fonte (scanner/celular)**
   • Resolução mínima: 300 DPI
   • Boa iluminação (evite sombras)
   • Documento bem posicionado
   • Evite reflexos e brilho

2. **Pré-processamento**
   • Use software de OCR antes (Adobe, ABBYY)
   • Ajuste contraste e brilho
   • Converta para preto e branco se possível

3. **Alternativa: Texto manual**
   • Se OCR falhar completamente
   • Copie e cole o texto no campo "Texto Manual"
   • IA ainda processará o conteúdo

**📄 Para PDFs digitais:**

1. **Verifique se é PDF digital**
   • Tente selecionar texto no leitor de PDF
   • Se não seleciona → é imagem

2. **Extração nativa**
   • PDFs digitais têm precisão 98%+
   • Erros são raros

**🔧 Após upload com erros:**

• Delete o documento com problemas
• Reprocesse com melhor qualidade
• Ou use a opção de texto manual

**🎯 Dicas avançadas:**

• Documentos manuscritos: OCR varia 50-80%
• Fontes decorativas: podem não ser reconhecidas
• Texto vertical: rotate antes de enviar
• Tabelas complexas: OCR pode ter dificuldade

**📞 Suporte:**
Para documentos importantes com OCR ruim, nossa equipe pode ajudar manualmente.`
  },
  {
    id: "cant-login",
    category: "Solução de Problemas",
    question: "Não consigo fazer login. O que fazer?",
    answer: `Soluções para problemas de login:

**🔴 Erro: "Usuário não encontrado"**
• Você já criou uma conta?
• Tente "Entrar com Google" se usou antes
• Verifique se usou o email correto

**🔴 Erro: "Senha incorreta"**
• Clique em "Esqueci minha senha"
• Link de redefinição enviado por email
• Verifique caixa de spam

**🔴 Erro: "Conta desativada"**
• Entre em contato: suporte@lexscan.ai
• Pode ter sido desativada por inatividade

**🔴 Página fica carregando...**
• Limpe cache do navegador (Ctrl+Shift+Delete)
• Tente modo anônimo (Ctrl+Shift+N)
• Desative extensões (AdBlock, uBlock)
• Tente outro navegador

**🔴 Botão de login não funciona**
• JavaScript pode estar desativado
• Ative em configurações do navegador
• Ou tente outro navegador

**🌐 Problemas com Google Login:**

1. Popup bloqueado?
   • Permita popups para lexscan.ai
   • Ícone no canto da barra de endereço

2. Conta Google errada?
   • Deslogue de outras contas Google
   • Ou use navegação anônima

3. Erro de permissão?
   • Acesse myaccount.google.com
   • Segurança > Aplicativos de terceiros
   • Remova LexScan e tente novamente

**📱 Problemas no celular:**
• Atualize o app do navegador
• Desative modo economia de dados
• Use WiFi em vez de 4G/5G

**🔧 Limpeza completa:**
~~~
1. Saia de todas as contas
2. Limpe cookies e cache
3. Feche o navegador
4. Abra novamente
5. Tente login
~~~

**📞 Ainda com problemas?**
Envie email para **suporte@lexscan.ai** com:
• Print do erro
• Navegador usado
• Sistema operacional`
  },

  // Categoria: Dicas e Truques
  {
    id: "productivity-tips",
    category: "Dicas e Truques",
    question: "Dicas para ser mais produtivo com o LexScan",
    answer: `Maximize sua produtividade:

**⚡ Upload Rápido**
• Use **Drag & Drop** (arrastar e soltar)
• Processe múltiplos documentos de uma vez
• Mantenha uma pasta "Para Processar" no desktop

**📅 Gestão de Prazos**
• Comece o dia olhando o **Calendário**
• Marque prazos como "Concluídos" quando cumprir
• Configure notificações 3 dias antes
• Sincronize com Google Calendar (em breve)

**💬 Chat Inteligente**
• Pergunte: "Resuma em 3 linhas" para visão rápida
• Use: "Quais os principais riscos?" para análise
• Exporte conversas importantes (em breve)

**📊 Organização**
• Use padrão de nomenclatura: TIPO_NUMERO_DATA.pdf
• Exemplo: PetInicial_12345_20240502.pdf
• Mantenha backup local dos originais

**📄 Relatórios**
• Gere relatório PDF para cada caso importante
• Envie a clientes como "Análise Técnica"
• Use relatório geral para reuniões de equipe

**🔄 Workflow sugerido:**
~~~
1. Café da manhã → Revisar Calendário de Prazos
2. Manhã → Processar documentos novos
3. Almoço → Verificar emails/notificações
4. Tarde → Chat com documentos para análise
5. Fim do dia → Exportar relatórios
~~~

**⌨️ Atalhos (em breve):**
• Ctrl+U: Upload rápido
• Ctrl+D: Dashboard
• Ctrl+C: Calendário
• Esc: Fechar modais

**📱 Mobile:**
• App PWA (instale na tela inicial)
• Tire fotos de documentos com celular
• Processe documentos em qualquer lugar

**🎯 Integrações (planos superiores):**
• Conecte com seu ERP
• API para integração com sistemas internos
• Webhooks para automações`
  },
  {
    id: "keyboard-shortcuts",
    category: "Dicas e Truques",
    question: "Existe atalhos de teclado?",
    answer: `Atalhos disponíveis (e em desenvolvimento):

**🎯 Atuais:**
• **Esc** - Fechar modais/abas
• **Ctrl+K** - Busca rápida (em breve)
• **?** - Abrir esta ajuda (em breve)

**⌨️ Em Desenvolvimento:**
• **Ctrl+U** - Upload de documento
• **Ctrl+D** - Ir para Dashboard
• **Ctrl+C** - Ir para Calendário
• **Ctrl+P** - Ir para Planos
• **Ctrl+/** - Foco no chat
• **Ctrl+N** - Novo documento

**🖱️ Atalhos de Mouse:**
• **Clique direito** em documento → Menu de ações
• **Duplo clique** em documento → Abrir detalhes
• **Scroll** no calendário → Navegar meses

**📱 Gestos Mobile:**
• **Swipe left** em documento → Deletar
• **Pull down** na lista → Atualizar
• **Pinch** no calendário → Zoom

**💡 Sugestão:**
Quer um atalho específico? Envie sugestão para **feedback@lexscan.ai**`
  }
];

const categories = [...new Set(faqData.map(item => item.category))];

export default function HelpPage() {
  const router = useRouter();
  const [activeCategory, setActiveCategory] = useState<string>("Começando");
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState("");

  const toggleItem = (id: string) => {
    const newOpen = new Set(openItems);
    if (newOpen.has(id)) {
      newOpen.delete(id);
    } else {
      newOpen.add(id);
    }
    setOpenItems(newOpen);
  };

  const filteredItems = faqData.filter(item => {
    const matchesCategory = item.category === activeCategory;
    const matchesSearch = searchTerm === "" ||
      item.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: colors.dark }}>
      <Sidebar />

      <main style={{ flex: 1, marginLeft: "260px", padding: "40px" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <h1 style={{ color: colors.light, fontSize: "36px", marginBottom: "8px" }}>
            ❓ Central de Ajuda
          </h1>
          <p style={{ color: colors.gray, fontSize: "16px" }}>
            Encontre respostas para todas as suas dúvidas
          </p>
        </div>

        {/* Search */}
        <div style={{ maxWidth: "600px", margin: "0 auto 40px" }}>
          <input
            type="text"
            placeholder="🔍 Buscar dúvidas..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: "100%",
              padding: "16px 20px",
              fontSize: "16px",
              borderRadius: "12px",
              border: "none",
              background: colors.primary,
              color: colors.light,
              outline: "none"
            }}
          />
        </div>

        {/* Categories */}
        <div style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "40px",
          justifyContent: "center"
        }}>
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              style={{
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                background: activeCategory === category ? colors.secondary : colors.primary,
                color: activeCategory === category ? colors.dark : colors.light,
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "bold",
                transition: "all 0.2s"
              }}
            >
              {category}
            </button>
          ))}
        </div>

        {/* FAQ Items */}
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          {filteredItems.length === 0 ? (
            <div style={{
              textAlign: "center",
              padding: "60px 20px",
              color: colors.gray
            }}>
              <p style={{ fontSize: "18px", marginBottom: "16px" }}>
                😕 Nenhum resultado encontrado
              </p>
              <p>Tente buscar com outros termos</p>
            </div>
          ) : (
            filteredItems.map((item, index) => (
              <div
                key={item.id}
                style={{
                  background: colors.primary,
                  borderRadius: "12px",
                  marginBottom: "16px",
                  overflow: "hidden",
                  animation: `fadeInUp 0.3s ease-out ${index * 0.05}s both`
                }}
              >
                <button
                  onClick={() => toggleItem(item.id)}
                  style={{
                    width: "100%",
                    padding: "20px 24px",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    cursor: "pointer",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    color: colors.light
                  }}
                >
                  <span style={{ fontSize: "16px", fontWeight: "600", flex: 1, paddingRight: "16px" }}>
                    {item.question}
                  </span>
                  <span style={{
                    fontSize: "20px",
                    transform: openItems.has(item.id) ? "rotate(180deg)" : "rotate(0)",
                    transition: "transform 0.3s"
                  }}>
                    ▼
                  </span>
                </button>

                {openItems.has(item.id) && (
                  <div style={{
                    padding: "0 24px 24px",
                    color: colors.light,
                    lineHeight: "1.8",
                    fontSize: "15px",
                    whiteSpace: "pre-wrap"
                  }}>
                    {item.answer}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Contact Section */}
        <div style={{
          maxWidth: "900px",
          margin: "60px auto 0",
          padding: "40px",
          background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.dark} 100%)`,
          borderRadius: "16px",
          border: `1px solid ${colors.secondary}40`
        }}>
          <h2 style={{ color: colors.light, fontSize: "24px", marginBottom: "16px", textAlign: "center" }}>
            🤔 Ainda tem dúvidas?
          </h2>
          <p style={{ color: colors.gray, textAlign: "center", marginBottom: "24px" }}>
            Nossa equipe está pronta para ajudar
          </p>

          <div style={{
            display: "flex",
            gap: "16px",
            justifyContent: "center",
            flexWrap: "wrap"
          }}>
            <a
              href="mailto:suporte@lexscan.ai"
              style={{
                padding: "14px 28px",
                background: colors.secondary,
                color: colors.dark,
                borderRadius: "8px",
                textDecoration: "none",
                fontWeight: "bold"
              }}
            >
              📧 Email de Suporte
            </a>
            <a
              href="https://wa.me/5511999999999"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                padding: "14px 28px",
                background: "transparent",
                border: `2px solid ${colors.secondary}`,
                color: colors.secondary,
                borderRadius: "8px",
                textDecoration: "none",
                fontWeight: "bold"
              }}
            >
              💬 WhatsApp
            </a>
          </div>

          <p style={{ color: colors.gray, textAlign: "center", marginTop: "20px", fontSize: "14px" }}>
            Horário de atendimento: Seg-Sex, 9h às 18h (BRT)
          </p>
        </div>

        {/* Back to Dashboard */}
        <div style={{ marginTop: "40px", textAlign: "center" }}>
          <button
            onClick={() => router.push("/dashboard")}
            style={{
              background: "transparent",
              border: "none",
              color: colors.gray,
              cursor: "pointer",
              fontSize: "14px"
            }}
          >
            ← Voltar para Dashboard
          </button>
        </div>
      </main>
    </div>
  );
}
