"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ProtectedRoute from "@/components/ProtectedRoute";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Message = {
  role: "user" | "ai";
  text: string;
  timestamp?: number;
};

type ChatHistory = {
  id: string;
  title: string;
  timestamp: number;
  preview: string;
};

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([
    { id: "1", title: "Planejamento de Marketing", timestamp: Date.now(), preview: "Como posso melhorar..." },
    { id: "2", title: "Análise de Vendas", timestamp: Date.now() - 86400000, preview: "Quais são as métricas..." },
    { id: "3", title: "Estratégia de Preços", timestamp: Date.now() - 172800000, preview: "Como definir preços..." },
  ]);

  const chatRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto scroll
  useEffect(() => {
    if (!chatRef.current) return;
    requestAnimationFrame(() => {
      chatRef.current!.scrollTop = chatRef.current!.scrollHeight;
    });
  }, [messages, loading]);

  const handleNewChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    setInput("");
  };

  const handleSelectChat = (chatId: string) => {
    setCurrentChatId(chatId);
    // Aqui carregaria as mensagens do histórico
    setMessages([]);
  };

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput("");
    setLoading(true);

    // Adiciona mensagem do usuário
    const newMessage: Message = {
      role: "user",
      text: userText,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, newMessage, { role: "ai", text: "" }]);

    // Cancela request anterior
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/chat-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) throw new Error("Erro na API");

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let aiText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        aiText += chunk;

        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = { role: "ai", text: aiText, timestamp: Date.now() };
          return copy;
        });
      }

      // Se for novo chat, adiciona ao histórico
      if (!currentChatId && messages.length === 0) {
        const newChat: ChatHistory = {
          id: Date.now().toString(),
          title: userText.slice(0, 30) + (userText.length > 30 ? "..." : ""),
          timestamp: Date.now(),
          preview: aiText.slice(0, 50) + "...",
        };
        setChatHistory((prev) => [newChat, ...prev]);
        setCurrentChatId(newChat.id);
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "❌ Erro ao conectar com a IA. Verifique o backend.", timestamp: Date.now() },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey && !loading) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <ProtectedRoute>
      <main className="chat-layout">
        <Sidebar
          chatHistory={chatHistory}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          currentChatId={currentChatId || undefined}
        />

        <div className="chat-main">
          {/* Header */}
          <header className="chat-header">
            <div className="header-info">
              <h1>💬 Chat</h1>
              {currentChatId && (
                <span className="chat-title">
                  {chatHistory.find((c) => c.id === currentChatId)?.title || "Nova conversa"}
                </span>
              )}
            </div>
            <div className="header-actions">
              <button className="header-btn" title="Exportar">
                📥
              </button>
              <button className="header-btn" title="Configurações" onClick={() => router.push("/settings")}>
                ⚙️
              </button>
            </div>
          </header>

          {/* Chat Area */}
          <div className="chat-container" ref={chatRef}>
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🧠</div>
                <h2>Como posso ajudar você hoje?</h2>
                <p>Envie uma mensagem para começar a conversar com a IA.</p>
                <div className="suggestions">
                  <button className="suggestion" onClick={() => setInput("Como posso melhorar minhas vendas?")}>
                    📈 Como posso melhorar minhas vendas?
                  </button>
                  <button className="suggestion" onClick={() => setInput("Analise meu fluxo de caixa")}>
                    💰 Analise meu fluxo de caixa
                  </button>
                  <button className="suggestion" onClick={() => setInput("Crie um plano de marketing")}>
                    📢 Crie um plano de marketing
                  </button>
                  <button className="suggestion" onClick={() => setInput("Quais as tendências do mercado?")}>
                    🔍 Quais as tendências do mercado?
                  </button>
                </div>
              </div>
            ) : (
              <div className="messages">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`message ${msg.role === "user" ? "user" : "ai"}`}
                  >
                    <div className="message-avatar">
                      {msg.role === "user" ? "👤" : "🧠"}
                    </div>
                    <div className="message-content">
                      <div className="message-text markdown-content">
                        {msg.text ? (
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.text}
                          </ReactMarkdown>
                        ) : loading && i === messages.length - 1 ? (
                          "Digitando..."
                        ) : (
                          ""
                        )}
                      </div>
                      {msg.timestamp && (
                        <div className="message-time">
                          {new Date(msg.timestamp).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && messages[messages.length - 1]?.text && (
                  <div className="message ai">
                    <div className="message-avatar">🧠</div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="input-container">
            <div className="input-wrapper">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Digite sua mensagem..."
                rows={1}
                disabled={loading}
              />
              <button
                className="send-btn"
                onClick={sendMessage}
                disabled={loading || !input.trim()}
              >
                {loading ? (
                  <span className="spinner" />
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                  </svg>
                )}
              </button>
            </div>
            <p className="input-hint">Pressione Enter para enviar, Shift + Enter para nova linha</p>
          </div>
        </div>

        <style jsx>{`
          .chat-layout {
            display: flex;
            height: 100vh;
            background: #020617;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          }

          .chat-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            margin-left: 280px;
          }

          .chat-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 24px;
            background: rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
          }

          .header-info {
            display: flex;
            align-items: center;
            gap: 12px;
          }

          .header-info h1 {
            font-size: 18px;
            font-weight: 600;
            margin: 0;
          }

          .chat-title {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.5);
            padding-left: 12px;
            border-left: 1px solid rgba(255, 255, 255, 0.2);
          }

          .header-actions {
            display: flex;
            gap: 8px;
          }

          .header-btn {
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: white;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 16px;
          }

          .header-btn:hover {
            background: rgba(255, 255, 255, 0.1);
          }

          .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
          }

          .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            max-width: 600px;
            margin: 0 auto;
          }

          .empty-icon {
            font-size: 64px;
            margin-bottom: 24px;
          }

          .empty-state h2 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 12px;
          }

          .empty-state p {
            font-size: 16px;
            color: rgba(255, 255, 255, 0.5);
            margin-bottom: 32px;
          }

          .suggestions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            width: 100%;
          }

          .suggestion {
            padding: 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            text-align: left;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 14px;
          }

          .suggestion:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(99, 102, 241, 0.5);
          }

          .messages {
            display: flex;
            flex-direction: column;
            gap: 16px;
            max-width: 800px;
            margin: 0 auto;
          }

          .message {
            display: flex;
            gap: 12px;
            align-items: flex-start;
          }

          .message.user {
            flex-direction: row-reverse;
          }

          .message-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
          }

          .message.user .message-avatar {
            background: linear-gradient(135deg, #4f46e5, #6366f1);
          }

          .message-content {
            max-width: calc(100% - 60px);
            padding: 14px 18px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.05);
          }

          .message.user .message-content {
            background: linear-gradient(135deg, #4f46e5, #6366f1);
          }

          .message-text {
            font-size: 15px;
            line-height: 1.6;
            word-break: break-word;
          }

          .message-time {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.4);
            margin-top: 6px;
          }

          .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 8px 0;
          }

          .typing-indicator span {
            width: 8px;
            height: 8px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
          }

          .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
          .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

          @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
          }

          .input-container {
            padding: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
          }

          .input-wrapper {
            display: flex;
            gap: 12px;
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 12px 16px;
          }

          .input-wrapper:focus-within {
            border-color: rgba(99, 102, 241, 0.5);
            background: rgba(255, 255, 255, 0.08);
          }

          .input-wrapper textarea {
            flex: 1;
            background: transparent;
            border: none;
            color: white;
            font-size: 15px;
            resize: none;
            outline: none;
            min-height: 24px;
            max-height: 200px;
            font-family: inherit;
          }

          .input-wrapper textarea::placeholder {
            color: rgba(255, 255, 255, 0.4);
          }

          .send-btn {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            border: none;
            border-radius: 10px;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            flex-shrink: 0;
          }

          .send-btn:hover:not(:disabled) {
            transform: scale(1.05);
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
          }

          .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
          }

          @keyframes spin {
            to { transform: rotate(360deg); }
          }

          .input-hint {
            text-align: center;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.3);
            margin-top: 12px;
          }

          /* MARKDOWN STYLES - Formatação de texto da IA */
          .markdown-content {
            line-height: 1.7;
          }

          .markdown-content h1,
          .markdown-content h2,
          .markdown-content h3,
          .markdown-content h4 {
            font-weight: 700;
            margin-top: 16px;
            margin-bottom: 12px;
            color: white;
          }

          .markdown-content h1 {
            font-size: 1.4em;
            border-bottom: 2px solid rgba(99, 102, 241, 0.5);
            padding-bottom: 8px;
          }

          .markdown-content h2 {
            font-size: 1.2em;
            color: #a5b4fc;
          }

          .markdown-content h3 {
            font-size: 1.1em;
            color: #c7d2fe;
          }

          .markdown-content p {
            margin-bottom: 12px;
            color: rgba(255, 255, 255, 0.9);
          }

          .markdown-content ul,
          .markdown-content ol {
            margin-left: 20px;
            margin-bottom: 12px;
          }

          .markdown-content li {
            margin-bottom: 6px;
            color: rgba(255, 255, 255, 0.85);
          }

          .markdown-content ul li {
            list-style-type: disc;
          }

          .markdown-content ol li {
            list-style-type: decimal;
          }

          .markdown-content strong {
            font-weight: 700;
            color: #a5b4fc;
          }

          .markdown-content em {
            font-style: italic;
            color: rgba(255, 255, 255, 0.8);
          }

          .markdown-content code {
            background: rgba(99, 102, 241, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
            color: #fbbf24;
          }

          .markdown-content pre {
            background: rgba(0, 0, 0, 0.4);
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 12px 0;
            border: 1px solid rgba(99, 102, 241, 0.2);
          }

          .markdown-content pre code {
            background: transparent;
            padding: 0;
            color: #e2e8f0;
          }

          .markdown-content blockquote {
            border-left: 4px solid #6366f1;
            padding-left: 16px;
            margin: 12px 0;
            color: rgba(255, 255, 255, 0.8);
            font-style: italic;
          }

          .markdown-content a {
            color: #818cf8;
            text-decoration: underline;
          }

          .markdown-content a:hover {
            color: #a5b4fc;
          }

          .markdown-content hr {
            border: none;
            border-top: 1px solid rgba(99, 102, 241, 0.3);
            margin: 20px 0;
          }

          .markdown-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
          }

          .markdown-content th,
          .markdown-content td {
            border: 1px solid rgba(99, 102, 241, 0.3);
            padding: 8px 12px;
            text-align: left;
          }

          .markdown-content th {
            background: rgba(99, 102, 241, 0.2);
            font-weight: 600;
          }

          @media (max-width: 768px) {
            .chat-main {
              margin-left: 0;
            }

            .suggestions {
              grid-template-columns: 1fr;
            }

            .message-content {
              max-width: calc(100% - 50px);
            }
          }
        `}</style>
      </main>
    </ProtectedRoute>
  );
}