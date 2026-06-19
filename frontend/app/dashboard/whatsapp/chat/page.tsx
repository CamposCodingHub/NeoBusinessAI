'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Conversation {
  phone: string;
  name: string;
  client_id: number | null;
  unread_count: number;
  last_message: string | null;
  last_message_at: string;
  message_count: number;
}

interface ChatMessage {
  id: number;
  sender_type: 'user' | 'client' | 'system' | 'bot';
  sender_name: string;
  sender_phone: string;
  message: string;
  message_type: string;
  is_read: boolean;
  is_from_whatsapp: boolean;
  created_at: string;
}

export default function WhatsAppChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedPhone, setSelectedPhone] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const getToken = () => {
    const tokensStr = localStorage.getItem('neobusiness_tokens');
    if (!tokensStr) return '';
    try {
      const tokens = JSON.parse(tokensStr);
      return tokens?.access_token || '';
    } catch { return ''; }
  };

  useEffect(() => {
    fetchConversations();
    // Polling a cada 30 segundos
    const interval = setInterval(fetchConversations, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedPhone) {
      fetchMessages(selectedPhone);
    }
  }, [selectedPhone]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchConversations = async () => {
    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/whatsapp/conversations`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Erro ao buscar conversas:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async (phone: string) => {
    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/whatsapp/messages/${encodeURIComponent(phone)}`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (error) {
      console.error('Erro ao buscar mensagens:', error);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedPhone || sending) return;

    setSending(true);
    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/whatsapp/send`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'omit',
        body: JSON.stringify({
          phone: selectedPhone,
          message: newMessage,
          context_type: 'general'
        })
      });

      if (response.ok) {
        setNewMessage('');
        // Atualizar mensagens
        fetchMessages(selectedPhone);
        fetchConversations();
      } else {
        alert('Erro ao enviar mensagem. Verifique se o WhatsApp está configurado.');
      }
    } catch (error) {
      console.error('Erro:', error);
    } finally {
      setSending(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Hoje';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Ontem';
    } else {
      return date.toLocaleDateString('pt-BR');
    }
  };

  const selectedConversation = conversations.find(c => c.phone === selectedPhone);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      {/* Header */}
      <div className="bg-white/5 border-b border-white/10 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition text-sm">
              ← Dashboard
            </Link>
            <Link href="/dashboard/whatsapp" className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition text-sm">
              ⚙️ Configuração
            </Link>
            <h1 className="text-xl font-bold text-green-400">💬 WhatsApp Chat</h1>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem('neobusiness_tokens');
              window.location.href = '/login';
            }}
            className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition text-sm"
          >
            Sair
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto flex h-[calc(100vh-80px)]">
        {/* Conversations List */}
        <div className="w-80 bg-white/5 border-r border-white/10 flex flex-col">
          <div className="p-4 border-b border-white/10">
            <h2 className="font-semibold">Conversas</h2>
            <p className="text-sm text-white/40">{conversations.length} contatos</p>
          </div>

          <div className="flex-1 overflow-y-auto">
            {conversations.length === 0 ? (
              <div className="p-4 text-center text-white/40">
                <p className="mb-2">📭 Nenhuma conversa</p>
                <p className="text-sm">Envie uma mensagem para iniciar</p>
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.phone}
                  onClick={() => setSelectedPhone(conv.phone)}
                  className={`w-full p-4 text-left border-b border-white/5 hover:bg-white/5 transition ${
                    selectedPhone === conv.phone ? 'bg-white/10' : ''
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium truncate">{conv.name}</span>
                    {conv.unread_count > 0 && (
                      <span className="px-2 py-0.5 bg-green-500 text-white text-xs rounded-full">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-white/50 truncate">{conv.last_message || 'Sem mensagens'}</p>
                  <p className="text-xs text-white/30 mt-1">
                    {conv.last_message_at ? formatDate(conv.last_message_at) : '-'}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {selectedPhone && selectedConversation ? (
            <>
              {/* Chat Header */}
              <div className="p-4 bg-white/5 border-b border-white/10 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{selectedConversation.name}</h3>
                  <p className="text-sm text-white/50">{selectedPhone}</p>
                </div>
                {selectedConversation.client_id && (
                  <Link
                    href={`/dashboard/clients/${selectedConversation.client_id}`}
                    className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm hover:bg-blue-500/30 transition"
                  >
                    Ver Cliente
                  </Link>
                )}
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 ? (
                  <div className="text-center text-white/40 py-12">
                    <p>Sem mensagens ainda</p>
                    <p className="text-sm mt-2">Envie a primeira mensagem!</p>
                  </div>
                ) : (
                  messages.map((msg, idx) => {
                    const isMe = msg.sender_type === 'user';
                    const showDate = idx === 0 ||
                      formatDate(msg.created_at) !== formatDate(messages[idx - 1].created_at);

                    return (
                      <div key={msg.id}>
                        {showDate && (
                          <div className="text-center my-4">
                            <span className="px-3 py-1 bg-white/10 rounded-full text-xs text-white/50">
                              {formatDate(msg.created_at)}
                            </span>
                          </div>
                        )}
                        <div className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[70%] px-4 py-2 rounded-2xl ${
                            isMe
                              ? 'bg-green-500/20 text-white rounded-br-none'
                              : 'bg-white/10 text-white rounded-bl-none'
                          }`}>
                            {!isMe && (
                              <p className="text-xs text-white/50 mb-1">{msg.sender_name}</p>
                            )}
                            <p>{msg.message}</p>
                            <p className={`text-xs mt-1 ${isMe ? 'text-green-400/70' : 'text-white/40'}`}>
                              {formatTime(msg.created_at)}
                              {isMe && msg.is_from_whatsapp && (
                                <span className="ml-2">✓</span>
                              )}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <form onSubmit={sendMessage} className="p-4 bg-white/5 border-t border-white/10">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Digite sua mensagem..."
                    className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-green-500/50"
                  />
                  <button
                    type="submit"
                    disabled={sending || !newMessage.trim()}
                    className="px-6 py-3 bg-green-500 hover:bg-green-600 disabled:bg-white/10 disabled:text-white/40 text-white rounded-xl font-semibold transition"
                  >
                    {sending ? '...' : 'Enviar'}
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-white/40">
              <div className="text-center">
                <p className="text-4xl mb-4">💬</p>
                <p>Selecione uma conversa para começar</p>
                <p className="text-sm mt-2 text-white/30">ou envie uma mensagem para um novo número</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
