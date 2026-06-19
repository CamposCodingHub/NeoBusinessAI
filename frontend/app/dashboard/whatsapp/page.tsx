'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface WhatsAppConfig {
  is_configured: boolean;
  is_active: boolean;
  is_connected: boolean;
  provider: string;
  phone_number?: string;
  auto_notify_deadlines: boolean;
  auto_notify_invoices: boolean;
  connected_at?: string;
}

export default function WhatsAppConfigPage() {
  const [config, setConfig] = useState<WhatsAppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState('');

  const [formData, setFormData] = useState({
    provider: 'twilio',
    twilio_account_sid: '',
    twilio_auth_token: '',
    twilio_phone_number: '',
    evolution_api_url: '',
    evolution_api_key: '',
    evolution_instance: '',
    auto_notify_deadlines: true,
    auto_notify_invoices: true
  });

  // Quick Setup states
  const [quickSetupLoading, setQuickSetupLoading] = useState(false);
  const [sandboxInfo, setSandboxInfo] = useState<any>(null);
  const [sendingTest, setSendingTest] = useState(false);

  const getToken = () => {
    const tokensStr = localStorage.getItem('neobusiness_tokens');
    if (!tokensStr) return '';
    try {
      const tokens = JSON.parse(tokensStr);
      return tokens?.access_token || '';
    } catch { return ''; }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    const token = getToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/whatsapp/config`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (response.ok) {
        const data = await response.json();
        setConfig(data);

        // Atualizar form se já tem config
        if (data.is_configured) {
          setFormData(prev => ({
            ...prev,
            provider: data.provider || 'twilio',
            auto_notify_deadlines: data.auto_notify_deadlines ?? true,
            auto_notify_invoices: data.auto_notify_invoices ?? true
          }));
        }
      }
    } catch (error) {
      console.error('Erro ao buscar config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');

    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/whatsapp/config`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'omit',
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(data.message);
        fetchConfig();
      } else {
        const error = await response.json();
        setMessage(`Erro: ${error.detail}`);
      }
    } catch (error) {
      setMessage('Erro ao salvar configuração');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage('');

    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/whatsapp/config/test`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      const data = await response.json();

      if (data.status === 'connected') {
        setMessage(`✅ ${data.message}`);
      } else {
        setMessage(`❌ ${data.message}`);
      }

      fetchConfig();
    } catch (error) {
      setMessage('❌ Erro ao testar conexão');
    } finally {
      setTesting(false);
    }
  };

  const handleQuickSetup = async () => {
    setQuickSetupLoading(true);
    setMessage('');

    const token = getToken();

    try {
      // Primeiro, buscar info do sandbox
      const infoResponse = await fetch(`${API_URL}/twilio-quick/sandbox-info`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (infoResponse.ok) {
        const infoData = await infoResponse.json();
        setSandboxInfo(infoData);
      }

      // Fazer setup rápido
      const setupResponse = await fetch(`${API_URL}/twilio-quick/setup`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'omit',
        body: JSON.stringify({ use_sandbox: true })
      });

      if (setupResponse.ok) {
        const data = await setupResponse.json();
        setMessage(`✅ ${data.message}`);
        fetchConfig();
      } else {
        const error = await setupResponse.json();
        setMessage(`❌ Erro: ${error.detail}`);
      }
    } catch (error) {
      setMessage('❌ Erro na configuração rápida');
    } finally {
      setQuickSetupLoading(false);
    }
  };

  const handleScheduleNotifications = async () => {
    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/whatsapp/schedule-deadline-notifications`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (response.ok) {
        const data = await response.json();
        alert(`${data.notifications_created} notificações de prazos agendadas!`);
      }
    } catch (error) {
      console.error('Erro:', error);
    }
  };

  const handleSendTestToUser = async () => {
    setSendingTest(true);

    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/twilio-quick/send-welcome-message`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          alert(`✅ Mensagem preparada!\n\nDestino: ${data.target_phone}\n\nClique no link para abrir o WhatsApp e ativar o sandbox:\n${data.direct_link}`);
        } else {
          alert(`⚠️ ${data.message}\n\nPassos:\n${data.instructions?.join('\n') || ''}`);
        }
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('❌ Erro ao enviar mensagem de teste');
    } finally {
      setSendingTest(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition text-sm">
              ← Voltar
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                Configuração WhatsApp
              </h1>
              <p className="text-white/60">Integração com Twilio ou Evolution API</p>
            </div>
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

        {/* Status Card */}
        {config && (
          <div className={`rounded-xl p-6 mb-6 ${
            config.is_connected
              ? 'bg-green-500/10 border border-green-500/50'
              : 'bg-amber-500/10 border border-amber-500/50'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold mb-1">
                  {config.is_connected ? '✅ WhatsApp Conectado' : '⚠️ WhatsApp Desconectado'}
                </h2>
                <p className="text-white/60">
                  {config.is_connected
                    ? `Conectado via ${config.provider.toUpperCase()}${config.phone_number ? ` (${config.phone_number})` : ''}`
                    : 'Configure suas credenciais para conectar'
                  }
                </p>
              </div>
              {config.is_connected && (
                <div className="text-right">
                  <p className="text-sm text-white/40">Conectado em</p>
                  <p className="text-green-400">
                    {config.connected_at
                      ? new Date(config.connected_at).toLocaleDateString('pt-BR')
                      : '-'
                    }
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* QUICK SETUP BUTTON */}
        {!config?.is_connected && (
          <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/50 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-green-400 mb-2">
                  🚀 Configuração Rápida - Modo Sandbox
                </h2>
                <p className="text-white/70">
                  Use nosso código sandbox pré-configurado para testar imediatamente!
                </p>
                <p className="text-sm text-green-400/80 mt-1">
                  Código: <strong>3VXXFT9RQK57SN8WYRC9ZRPM</strong>
                </p>
              </div>
              <button
                onClick={handleQuickSetup}
                disabled={quickSetupLoading}
                className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-xl font-semibold transition flex items-center gap-2"
              >
                {quickSetupLoading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Configurando...
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    Ativar Agora
                  </>
                )}
              </button>
            </div>

            {sandboxInfo && (
              <div className="mt-4 p-4 bg-white/10 rounded-xl">
                <h3 className="font-semibold mb-3">📱 Passo a passo:</h3>
                <div className="space-y-3">
                  {sandboxInfo.instructions.map((inst: any) => (
                    <div key={inst.step} className="flex items-start gap-3">
                      <span className="w-8 h-8 bg-green-500/30 text-green-400 rounded-full flex items-center justify-center font-bold text-sm shrink-0">
                        {inst.step}
                      </span>
                      <div>
                        <p className="font-medium">{inst.title}</p>
                        <p className="text-sm text-white/60">{inst.description}</p>
                        {inst.copy_text && (
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(inst.copy_text);
                              alert('Texto copiado! Cole no WhatsApp.');
                            }}
                            className="mt-2 px-3 py-1 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded text-sm transition"
                          >
                            📋 Copiar mensagem
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-blue-500/20 rounded-lg">
                  <p className="text-sm text-blue-400">
                    💡 <strong>Dica:</strong> Clique no botão abaixo para abrir o WhatsApp diretamente:
                  </p>
                  <a
                    href={sandboxInfo.direct_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition"
                  >
                    📱 Abrir WhatsApp
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Message */}
        {message && (
          <div className={`p-4 rounded-xl mb-6 ${
            message.includes('✅')
              ? 'bg-green-500/10 border border-green-500/50 text-green-400'
              : 'bg-red-500/10 border border-red-500/50 text-red-400'
          }`}>
            {message}
          </div>
        )}

        {/* Config Form */}
        <div className="bg-white/5 rounded-xl p-6 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Configuração</h2>
            <button
              onClick={handleTest}
              disabled={testing}
              className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition text-sm"
            >
              {testing ? 'Testando...' : 'Testar Conexão'}
            </button>
          </div>

          <form onSubmit={handleSave} className="space-y-4">
            {/* Provider Selection */}
            <div>
              <label className="block text-sm text-white/60 mb-2">Provedor</label>
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, provider: 'twilio' })}
                  className={`flex-1 p-4 rounded-xl border transition text-left ${
                    formData.provider === 'twilio'
                      ? 'bg-blue-500/20 border-blue-500/50'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <p className="font-semibold">Twilio</p>
                  <p className="text-sm text-white/50">API oficial, mais estável</p>
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, provider: 'evolution_api' })}
                  className={`flex-1 p-4 rounded-xl border transition text-left ${
                    formData.provider === 'evolution_api'
                      ? 'bg-green-500/20 border-green-500/50'
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                >
                  <p className="font-semibold">Evolution API</p>
                  <p className="text-sm text-white/50">Self-hosted, sem custo por mensagem</p>
                </button>
              </div>
            </div>

            {/* Twilio Config */}
            {formData.provider === 'twilio' && (
              <div className="space-y-4 p-4 bg-blue-500/5 rounded-xl">
                <div>
                  <label className="block text-sm text-white/60 mb-2">Account SID</label>
                  <input
                    type="text"
                    value={formData.twilio_account_sid}
                    onChange={(e) => setFormData({ ...formData, twilio_account_sid: e.target.value })}
                    placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-2">Auth Token</label>
                  <input
                    type="password"
                    value={formData.twilio_auth_token}
                    onChange={(e) => setFormData({ ...formData, twilio_auth_token: e.target.value })}
                    placeholder="••••••••••••••••••••••••"
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-2">Número do WhatsApp (formato: +55...)</label>
                  <input
                    type="text"
                    value={formData.twilio_phone_number}
                    onChange={(e) => setFormData({ ...formData, twilio_phone_number: e.target.value })}
                    placeholder="+5511999999999"
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-blue-500/50"
                  />
                </div>
              </div>
            )}

            {/* Evolution API Config */}
            {formData.provider === 'evolution_api' && (
              <div className="space-y-4 p-4 bg-green-500/5 rounded-xl">
                <div>
                  <label className="block text-sm text-white/60 mb-2">URL da API</label>
                  <input
                    type="url"
                    value={formData.evolution_api_url}
                    onChange={(e) => setFormData({ ...formData, evolution_api_url: e.target.value })}
                    placeholder="https://evolution.seudominio.com"
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-2">API Key</label>
                  <input
                    type="password"
                    value={formData.evolution_api_key}
                    onChange={(e) => setFormData({ ...formData, evolution_api_key: e.target.value })}
                    placeholder="••••••••••••••••••••••••"
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50"
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/60 mb-2">Nome da Instância</label>
                  <input
                    type="text"
                    value={formData.evolution_instance}
                    onChange={(e) => setFormData({ ...formData, evolution_instance: e.target.value })}
                    placeholder="jurisflow"
                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50"
                  />
                </div>
              </div>
            )}

            {/* Auto Notifications */}
            <div className="p-4 bg-white/5 rounded-xl">
              <h3 className="font-semibold mb-3">Notificações Automáticas</h3>
              <div className="space-y-2">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={formData.auto_notify_deadlines}
                    onChange={(e) => setFormData({ ...formData, auto_notify_deadlines: e.target.checked })}
                    className="w-5 h-5 rounded bg-white/10 border-white/30"
                  />
                  <span>Enviar lembretes automáticos de prazos para clientes</span>
                </label>
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={formData.auto_notify_invoices}
                    onChange={(e) => setFormData({ ...formData, auto_notify_invoices: e.target.checked })}
                    className="w-5 h-5 rounded bg-white/10 border-white/30"
                  />
                  <span>Enviar lembretes de faturas/cobranças</span>
                </label>
              </div>
            </div>

            {/* Submit */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl font-semibold hover:opacity-90 transition"
              >
                {saving ? 'Salvando...' : 'Salvar Configuração'}
              </button>
            </div>
          </form>
        </div>

        {/* Quick Actions */}
        {config?.is_connected && (
          <div className="bg-white/5 rounded-xl p-6">
            <h2 className="text-xl font-semibold mb-4">Ações Rápidas</h2>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/dashboard/whatsapp/chat"
                className="px-6 py-3 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-xl transition"
              >
                💬 Abrir Chat
              </Link>
              <button
                onClick={handleScheduleNotifications}
                className="px-6 py-3 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-xl transition"
              >
                📅 Agendar Notificações
              </button>
              <button
                onClick={handleSendTestToUser}
                disabled={sendingTest}
                className="px-6 py-3 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-xl transition disabled:opacity-50"
              >
                {sendingTest ? '⏳ Enviando...' : '📱 Testar Meu Número'}
              </button>
            </div>

            {/* User phone info */}
            <div className="mt-4 p-3 bg-white/5 rounded-lg">
              <p className="text-sm text-white/60">Seu número configurado:</p>
              <p className="text-lg font-semibold text-green-400">+55 17 99207-7312</p>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-6 bg-white/5 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">📖 Como Configurar</h2>

          {formData.provider === 'twilio' ? (
            <div className="space-y-2 text-white/70 text-sm">
              <p><strong>1.</strong> Crie uma conta em <a href="https://www.twilio.com" target="_blank" className="text-blue-400 hover:underline">twilio.com</a></p>
              <p><strong>2.</strong> Ative o <strong>Twilio Sandbox for WhatsApp</strong> no console</p>
              <p><strong>3.</strong> Copie seu <strong>Account SID</strong> e <strong>Auth Token</strong> da página principal</p>
              <p><strong>4.</strong> No Sandbox, copie o número do WhatsApp fornecido (ex: +14155238886)</p>
              <p><strong>5.</strong> Cole os dados acima e salve</p>
              <p className="text-amber-400 mt-4">⚠️ Para enviar mensagens, o cliente precisa primeiro enviar "join [seu-código]" para o número do Twilio</p>
            </div>
          ) : (
            <div className="space-y-2 text-white/70 text-sm">
              <p><strong>1.</strong> Instale o Evolution API em seu servidor</p>
              <p><strong>2.</strong> Crie uma instância no painel do Evolution</p>
              <p><strong>3.</strong> Escaneie o QR Code com seu WhatsApp</p>
              <p><strong>4.</strong> Copie a URL da API, API Key e nome da instância</p>
              <p><strong>5.</strong> Cole os dados acima e salve</p>
              <p className="text-green-400 mt-4">✅ Sem custo por mensagem! Ideal para alto volume</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
