/*
🎨 PREMIUM CHAT INTERFACE - LexScan IA
Componente de Chat com UX Premium, Streaming e Animações

Implementa:
- Streaming de respostas
- Efeito digitando
- Markdown bonito
- Animações suaves
- Design premium
*/

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  Clock,
  CheckCircle2
} from 'lucide-react';

// Tipos
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  metadata?: {
    qualityScore?: number;
    style?: string;
    detectedIntent?: string;
  };
}

interface PremiumChatProps {
  documentId?: string;
  userId: string;
  onClose?: () => void;
}

// Componente principal
export const PremiumChat: React.FC<PremiumChatProps> = ({
  documentId,
  userId,
  onClose
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: '👋 Olá! Sou o Lex, seu assistente jurídico inteligente.\n\nComo posso ajudar você com este documento hoje? Posso:\n\n• 📄 Analisar cláusulas e riscos\n• ⚖️ Explicar termos jurídicos\n• 📅 Identificar prazos importantes\n• 💡 Sugerir estratégias\n\n**O que você gostaria de saber?**',
      timestamp: new Date(),
      metadata: { style: 'welcome' }
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll para última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = inputRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setIsTyping(true);

    // Simular delay de processamento
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Mensagem da IA em streaming
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      metadata: {
        qualityScore: 92,
        style: 'analytical',
        detectedIntent: 'seeking_knowledge'
      }
    };

    setMessages(prev => [...prev, assistantMessage]);

    // Simular streaming de resposta
    const fullResponse = generateMockResponse(input);
    let currentIndex = 0;

    const streamInterval = setInterval(() => {
      if (currentIndex < fullResponse.length) {
        const chunk = fullResponse.slice(0, currentIndex + 3);
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMessage.id
              ? { ...msg, content: chunk }
              : msg
          )
        );
        currentIndex += 3;
      } else {
        clearInterval(streamInterval);
        setIsLoading(false);
        setIsTyping(false);
        setMessages(prev =>
          prev.map(msg =>
            msg.id === assistantMessage.id
              ? { ...msg, isStreaming: false }
              : msg
          )
        );
      }
    }, 30);
  };

  const generateMockResponse = (query: string): string => {
    // Simulação de resposta contextual
    if (query.toLowerCase().includes('prazo')) {
      return `📅 **Análise de Prazos Encontrada**

Com base no documento analisado, identifiquei **3 prazos críticos**:

**1. Prazo de Recurso (Art. 1.012 CPC)**
• 📆 Data: 15 dias úteis após intimação
• ⚠️ Status: 🟡 URGENTE
• 💡 Recomendação: Monitorar de perto

**2. Prazo para Contestação**
• 📆 Data: 15 dias (parte autora)
• ⚠️ Status: 🟢 DENTRO DO PRAZO

**3. Prazo de Audiência**
• 📆 Data: 30/05/2026 às 14h
• 📍 Local: 3ª Vara Cível

**⚡ Ações Recomendadas:**
1. Agendar alerta 3 dias antes
2. Preparar memória para recurso
3. Confirmar disponibilidade de testemunhas

Você gostaria de aprofundar em algum desses prazos específicos?`;
    }

    return `💡 **Análise Completa do Documento**

${query.includes('contrato') ? 'Analisando as cláusulas contratuais...' : 'Analisando seu questionamento...'}

**Pontos Principais:**

✅ **Aspectos Positivos**
• Documento bem estruturado juridicamente
• Cláusulas claras e objetivas
• Proteções adequadas para ambas as partes

⚠️ **Pontos de Atenção**
• Cláusula de rescisão pode ser mais específica
• Prazos de notificação podem ser encurtados
• Falta previsão para força maior

**🎯 Recomendações Estratégicas:**

1. **Solicitar esclarecimento** sobre a cláusula X
2. **Negociar prazo** de pagamento para 30 dias
3. **Incluir cláusula** de renegociação automática

Quer que eu prepare uma minuta de sugestões para enviar à outra parte?`;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 rounded-2xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-700">
      {/* Header */}
      <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-lg border-b border-slate-200 dark:border-slate-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              Lex AI
              <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs rounded-full">
                Premium
              </span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Online • Respostas inteligentes ativadas
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
                message.role === 'assistant'
                  ? 'bg-gradient-to-br from-blue-500 to-purple-600'
                  : 'bg-slate-200 dark:bg-slate-700'
              }`}>
                {message.role === 'assistant' ? (
                  <Bot className="w-5 h-5 text-white" />
                ) : (
                  <User className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                )}
              </div>

              {/* Message Bubble */}
              <div className={`max-w-[80%] ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-5 py-3 rounded-2xl ${
                  message.role === 'assistant'
                    ? 'bg-white dark:bg-slate-700 shadow-lg border border-slate-100 dark:border-slate-600'
                    : 'bg-blue-500 text-white'
                }`}>
                  {message.role === 'assistant' ? (
                    <div className="prose prose-slate dark:prose-invert max-w-none">
                      <ReactMarkdown
                        components={{
                          code({ node, inline, className, children, ...props }: any) {
                            const match = /language-(\w+)/.exec(className || '');
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={vscDarkPlus}
                                language={match[1]}
                                PreTag="div"
                                {...props}
                              >
                                {String(children).replace(/\n$/, '')}
                              </SyntaxHighlighter>
                            ) : (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          }
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>

                      {/* Efeito digitando */}
                      {message.isStreaming && (
                        <span className="inline-flex items-center gap-1 ml-1">
                          <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                          <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                          <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.4s]" />
                        </span>
                      )}
                    </div>
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                </div>

                {/* Metadata */}
                <div className="flex items-center gap-2 mt-2 px-1">
                  <span className="text-xs text-slate-400">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>

                  {message.metadata?.qualityScore && (
                    <span className="flex items-center gap-1 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                      <Sparkles className="w-3 h-3" />
                      {message.metadata.qualityScore}% match
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing Indicator */}
        {isTyping && !isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-3 text-slate-500"
          >
            <div className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-full">
              <span className="text-sm">Lex está pensando</span>
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]" />
              </span>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua pergunta sobre o documento..."
              className="w-full px-4 py-3 bg-slate-100 dark:bg-slate-700 rounded-xl border-0 focus:ring-2 focus:ring-blue-500 resize-none max-h-32 text-slate-900 dark:text-white placeholder-slate-400"
              rows={1}
              disabled={isLoading}
            />
            <div className="absolute bottom-2 right-2 text-xs text-slate-400">
              {input.length}/500
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={`p-3 rounded-xl transition-all ${
              input.trim() && !isLoading
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg hover:shadow-xl'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
            }`}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 mt-3 overflow-x-auto pb-2">
          {['📅 Quais prazos?', '⚖️ Análise de riscos', '💡 Sugestões', '📄 Resumo'].map((action) => (
            <button
              key={action}
              onClick={() => setInput(action.replace(/[📅⚖️💡📄] /, ''))}
              className="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-full text-xs text-slate-600 dark:text-slate-300 transition-colors whitespace-nowrap"
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PremiumChat;
