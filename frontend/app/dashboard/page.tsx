'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const API_URL = 'http://127.0.0.1:8000';

interface Document {
  id: number;
  filename: string;
  status: string;
  created_at: string;
}

interface DeadlineAlert {
  deadline_id: number;
  description: string;
  due_date: string;
  days_until: number;
  alert_level: 'overdue' | 'critical' | 'high' | 'medium' | 'low';
  alert_message: string;
}

interface DeadlineStats {
  overview: {
    total: number;
    pending: number;
    completed: number;
  };
  alerts: {
    overdue: number;
    due_today: number;
    due_tomorrow: number;
    due_this_week: number;
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [deadlineStats, setDeadlineStats] = useState<DeadlineStats | null>(null);
  const [alerts, setAlerts] = useState<DeadlineAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch dados UMA VEZ na montagem
  useEffect(() => {
    // Ler token da chave correta usada pelo AuthContext
    const tokensStr = localStorage.getItem('neobusiness_tokens');
    let token = '';
    try {
      const tokens = tokensStr ? JSON.parse(tokensStr) : null;
      token = tokens?.access_token || '';
    } catch { token = ''; }

    if (!token) {
      window.location.href = '/login';
      return;
    }

    // Buscar dados do usuário
    fetch(`${API_URL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'omit'
    })
    .then(res => res.ok ? res.json() : Promise.reject('Erro ao buscar usuário'))
    .then(data => setUser(data))
    .catch(err => setError(String(err)));

    // Buscar documentos
    fetch(`${API_URL}/documents/`, {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'omit'
    })
    .then(res => res.ok ? res.json() : Promise.reject('Erro ao buscar documentos'))
    .then(data => setDocuments(data.documents || []))
    .catch(err => console.error(err));

    // Buscar estatísticas de prazos
    fetch(`${API_URL}/deadlines/stats/overview`, {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'omit'
    })
    .then(res => res.ok ? res.json() : Promise.reject('Erro ao buscar estatísticas'))
    .then(data => setDeadlineStats(data))
    .catch(err => console.error('Erro stats prazos:', err));

    // Buscar alertas de prazos
    fetch(`${API_URL}/deadlines/alerts/upcoming?days=30`, {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'omit'
    })
    .then(res => res.ok ? res.json() : Promise.reject('Erro ao buscar alertas'))
    .then(data => setAlerts(data.alerts || []))
    .catch(err => console.error('Erro alertas:', err))
    .finally(() => setLoading(false));
  }, []);

  const handleUpload = () => router.push('/dashboard/documents');
  const handleChat = () => router.push('/chat');

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  const completedDocs = documents.filter(d => d.status === 'completed').length;
  const hoursSaved = completedDocs * 2;

  // Alertas críticos
  const criticalAlerts = alerts.filter(a => a.alert_level === 'critical' || a.alert_level === 'overdue');
  const highAlerts = alerts.filter(a => a.alert_level === 'high');

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-white/60 mt-1">
            Bem-vindo, {user?.name || 'Usuário'}! • {new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-white/40 text-sm">{new Date().toLocaleTimeString('pt-BR')}</p>
            <p className="text-cyan-400 text-sm">{user?.role || 'user'}</p>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem('neobusiness_tokens');
              localStorage.removeItem('neobusiness_user');
              window.location.href = '/login';
            }}
            className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition text-sm"
          >
            Sair
          </button>
        </div>
      </div>

      {/* ALERTAS CRÍTICOS */}
      {(criticalAlerts.length > 0 || (deadlineStats?.alerts?.overdue ?? 0) > 0) && (
        <div className="mb-6 bg-red-500/10 border border-red-500/50 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-red-400 flex items-center gap-2">
              🚨 ALERTAS CRÍTICOS DE PRAZOS
            </h2>
            <Link href="/dashboard/deadlines" className="text-red-400 text-sm hover:underline">
              Ver todos →
            </Link>
          </div>
          <div className="flex flex-wrap gap-3">
            {(deadlineStats?.alerts?.overdue ?? 0) > 0 && (
              <span className="px-4 py-2 bg-red-500 text-white rounded-lg font-bold">
                {deadlineStats?.alerts?.overdue} Atrasados
              </span>
            )}
            {(deadlineStats?.alerts?.due_today ?? 0) > 0 && (
              <span className="px-4 py-2 bg-red-500/80 text-white rounded-lg font-bold">
                {deadlineStats?.alerts?.due_today} Vence Hoje
              </span>
            )}
            {(deadlineStats?.alerts?.due_tomorrow ?? 0) > 0 && (
              <span className="px-4 py-2 bg-amber-500 text-white rounded-lg font-bold">
                {deadlineStats?.alerts?.due_tomorrow} Amanhã
              </span>
            )}
            {criticalAlerts.slice(0, 3).map(alert => (
              <span key={alert.deadline_id} className="px-3 py-2 bg-red-500/20 text-red-400 rounded-lg text-sm">
                {alert.alert_message}: {alert.description}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <Link href="/dashboard/deadlines" className="bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-xl p-4 transition">
          <p className="text-red-400 text-sm mb-1">🔴 Prazos Atrasados</p>
          <p className="text-3xl font-bold text-red-400">{deadlineStats?.alerts?.overdue || 0}</p>
          <p className="text-white/40 text-xs mt-1">Requerem ação imediata</p>
        </Link>
        <Link href="/dashboard/deadlines" className="bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-xl p-4 transition">
          <p className="text-amber-400 text-sm mb-1">⚠️ Esta Semana</p>
          <p className="text-3xl font-bold text-amber-400">{(deadlineStats?.alerts?.due_today || 0) + (deadlineStats?.alerts?.due_tomorrow || 0) + (deadlineStats?.alerts?.due_this_week || 0)}</p>
          <p className="text-white/40 text-xs mt-1">Hoje + Amanhã + Semana</p>
        </Link>
        <StatCard icon="📄" label="Documentos" value={documents.length} />
        <StatCard icon="⚖️" label="Peças Geradas" value={Math.floor(documents.length * 0.3)} />
        <StatCard icon="⏱️" label="Tempo Economizado" value={`${hoursSaved}h`} />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PRAZOS - NOVO */}
        <div className="lg:col-span-2 bg-white/5 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">⚠️ Prazos Prioritários</h2>
            <Link href="/dashboard/deadlines" className="text-cyan-400 text-sm hover:underline">
              Gerenciar prazos →
            </Link>
          </div>

          {alerts.length === 0 ? (
            <div className="text-center py-8 text-white/40">
              <p className="mb-4">🎉 Nenhum prazo urgente!</p>
              <Link href="/dashboard/deadlines" className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded-lg transition inline-block">
                Ver todos os prazos
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {alerts.slice(0, 5).map(alert => (
                <div key={alert.deadline_id} className={`flex items-center justify-between p-3 rounded-lg transition ${
                  alert.alert_level === 'critical' || alert.alert_level === 'overdue'
                    ? 'bg-red-500/10 border border-red-500/30'
                    : alert.alert_level === 'high'
                    ? 'bg-amber-500/10 border border-amber-500/30'
                    : 'bg-white/5 hover:bg-white/10'
                }`}>
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      alert.alert_level === 'critical' ? 'bg-red-500 text-white' :
                      alert.alert_level === 'overdue' ? 'bg-red-600 text-white' :
                      alert.alert_level === 'high' ? 'bg-amber-500 text-black' :
                      'bg-cyan-500/20 text-cyan-400'
                    }`}>
                      {alert.alert_message}
                    </span>
                    <div>
                      <p className="font-medium text-white">{alert.description}</p>
                      <p className="text-sm text-white/40">Vence: {new Date(alert.due_date).toLocaleDateString('pt-BR')}</p>
                    </div>
                  </div>
                </div>
              ))}
              {alerts.length > 5 && (
                <p className="text-center text-white/40 text-sm py-2">
                  +{alerts.length - 5} prazos adicionais
                </p>
              )}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white/5 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Ações Rápidas</h2>
          <div className="space-y-3">
            <ActionButton icon="📅" label="Controle de Prazos" onClick={() => router.push('/dashboard/deadlines')} color="red" />
            <ActionButton icon="👥" label="Clientes" onClick={() => router.push('/dashboard/clients')} color="blue" />
            <ActionButton icon="💰" label="Financeiro" onClick={() => router.push('/dashboard/finance')} color="emerald" />
            <ActionButton icon="💬" label="WhatsApp" onClick={() => router.push('/dashboard/whatsapp/chat')} color="green" />
            <ActionButton icon="🤖" label="Chat Jurídico IA" onClick={handleChat} color="cyan" />
            <ActionButton icon="📤" label="Upload Documento" onClick={handleUpload} color="purple" />
            <ActionButton icon="⚖️" label="Gerar Peça Jurídica" onClick={() => router.push('/dashboard/legal')} color="pink" />
            <ActionButton icon="📊" label="Relatórios" onClick={() => router.push('/dashboard/reports')} color="amber" />
          </div>
        </div>
      </div>

      {/* Documentos Section (Abaixo) */}
      <div className="mt-6 bg-white/5 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">📄 Documentos Recentes</h2>
          <Link href="/dashboard/documents" className="text-cyan-400 text-sm hover:underline">
            Ver todos →
          </Link>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-8 text-white/40">
            <p className="mb-4">Nenhum documento ainda</p>
            <button
              onClick={handleUpload}
              className="px-4 py-2 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded-lg transition"
            >
              Fazer primeiro upload
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.slice(0, 5).map(doc => (
              <div key={doc.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${doc.status === 'completed' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                  <div>
                    <p className="font-medium text-white">{doc.filename}</p>
                    <p className="text-sm text-white/40">{doc.status}</p>
                  </div>
                </div>
                <span className="text-white/40 text-sm">{new Date(doc.created_at).toLocaleDateString('pt-BR')}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
function StatCard({ icon, label, value }: { icon: string; label: string; value: string | number }) {
  return (
    <div className="bg-white/5 rounded-xl p-4 hover:bg-white/10 transition">
      <div className="text-2xl mb-2">{icon}</div>
      <p className="text-white/60 text-sm">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function ActionButton({ icon, label, onClick, color }: { icon: string; label: string; onClick: () => void; color: string }) {
  const colors: Record<string, string> = {
    cyan: 'hover:bg-cyan-500/20 text-cyan-400',
    purple: 'hover:bg-purple-500/20 text-purple-400',
    pink: 'hover:bg-pink-500/20 text-pink-400',
    emerald: 'hover:bg-emerald-500/20 text-emerald-400',
    red: 'hover:bg-red-500/20 text-red-400',
    blue: 'hover:bg-blue-500/20 text-blue-400',
    amber: 'hover:bg-amber-500/20 text-amber-400',
    green: 'hover:bg-green-500/20 text-green-400',
  };

  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-3 bg-white/5 rounded-lg ${colors[color]} transition text-left`}
    >
      <span className="text-xl">{icon}</span>
      <span>{label}</span>
    </button>
  );
}
