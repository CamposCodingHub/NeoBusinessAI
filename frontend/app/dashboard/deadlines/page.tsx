'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Deadline {
  id: number;
  description: string;
  due_date: string;
  days: number;
  urgency: 'high' | 'medium' | 'low';
  context: string;
  is_completed: boolean;
  created_at: string;
}

interface Alert {
  deadline_id: number;
  description: string;
  due_date: string;
  days_until: number;
  alert_level: 'overdue' | 'critical' | 'high' | 'medium' | 'low';
  alert_message: string;
  context: string;
}

export default function DeadlinesPage() {
  const [deadlines, setDeadlines] = useState<Deadline[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('pending');

  // Form state
  const [formData, setFormData] = useState({
    description: '',
    days: 15,
    due_date: '',
    urgency: 'medium',
    context: ''
  });

  const getToken = () => {
    const tokensStr = localStorage.getItem('neobusiness_tokens');
    if (!tokensStr) return '';
    try {
      const tokens = JSON.parse(tokensStr);
      return tokens?.access_token || '';
    } catch { return ''; }
  };

  useEffect(() => {
    const token = getToken();
    if (!token) {
      window.location.href = '/login';
      return;
    }

    fetchDeadlines();
    fetchAlerts();
    fetchStats();
  }, [filter]);

  const fetchDeadlines = async () => {
    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/deadlines/?status=${filter}`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (response.ok) {
        const data = await response.json();
        setDeadlines(data.deadlines || []);
      }
    } catch (error) {
      console.error('Erro ao buscar prazos:', error);
    }
  };

  const fetchAlerts = async () => {
    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/deadlines/alerts/upcoming?days=30`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error('Erro ao buscar alertas:', error);
    }
  };

  const fetchStats = async () => {
    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/deadlines/stats/overview`, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Erro ao buscar estatísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/deadlines/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'omit',
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowForm(false);
        setFormData({ description: '', days: 15, due_date: '', urgency: 'medium', context: '' });
        fetchDeadlines();
        fetchAlerts();
        fetchStats();
      }
    } catch (error) {
      console.error('Erro ao criar prazo:', error);
    }
  };

  const handleComplete = async (id: number) => {
    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/deadlines/${id}/complete`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (response.ok) {
        fetchDeadlines();
        fetchStats();
      }
    } catch (error) {
      console.error('Erro ao concluir prazo:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja excluir este prazo?')) return;

    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/deadlines/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });

      if (response.ok) {
        fetchDeadlines();
        fetchStats();
      }
    } catch (error) {
      console.error('Erro ao excluir prazo:', error);
    }
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'overdue': return 'bg-red-500 text-white';
      case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'high': return 'bg-amber-500/20 text-amber-400 border-amber-500/50';
      case 'medium': return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50';
      default: return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'text-red-400 bg-red-500/20';
      case 'medium': return 'text-amber-400 bg-amber-500/20';
      default: return 'text-emerald-400 bg-emerald-500/20';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition text-sm">
              ← Voltar
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                Controle de Prazos
              </h1>
              <p className="text-white/60">Gerencie todos os prazos processuais</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-semibold hover:opacity-90 transition"
            >
              + Novo Prazo
            </button>
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

        {/* Stats Overview */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-white/5 rounded-xl p-4">
              <p className="text-white/60 text-sm">Total</p>
              <p className="text-2xl font-bold">{stats.overview.total}</p>
            </div>
            <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/30">
              <p className="text-red-400 text-sm">Atrasados</p>
              <p className="text-2xl font-bold text-red-400">{stats.alerts.overdue}</p>
            </div>
            <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/30">
              <p className="text-red-400 text-sm">Hoje/Amanhã</p>
              <p className="text-2xl font-bold text-red-400">{stats.alerts.due_today + stats.alerts.due_tomorrow}</p>
            </div>
            <div className="bg-amber-500/10 rounded-xl p-4 border border-amber-500/30">
              <p className="text-amber-400 text-sm">Esta Semana</p>
              <p className="text-2xl font-bold text-amber-400">{stats.alerts.due_this_week}</p>
            </div>
            <div className="bg-emerald-500/10 rounded-xl p-4 border border-emerald-500/30">
              <p className="text-emerald-400 text-sm">Concluídos</p>
              <p className="text-2xl font-bold text-emerald-400">{stats.overview.completed}</p>
            </div>
          </div>
        )}

        {/* Critical Alerts */}
        {alerts.filter(a => a.alert_level === 'critical' || a.alert_level === 'overdue').length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3 text-red-400">⚠️ Alertas Críticos</h2>
            <div className="space-y-2">
              {alerts
                .filter(a => a.alert_level === 'critical' || a.alert_level === 'overdue')
                .map(alert => (
                  <div key={alert.deadline_id} className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="px-3 py-1 bg-red-500 text-white rounded-lg text-sm font-bold">
                        {alert.alert_message}
                      </span>
                      <div>
                        <p className="font-semibold">{alert.description}</p>
                        <p className="text-white/50 text-sm">{alert.context}</p>
                      </div>
                    </div>
                    <button
                      onClick={() => handleComplete(alert.deadline_id)}
                      className="px-4 py-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg transition text-sm"
                    >
                      Concluir
                    </button>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {(['pending', 'completed', 'all'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg transition ${
                filter === f
                  ? 'bg-cyan-500/30 text-cyan-400 border border-cyan-500/50'
                  : 'bg-white/5 text-white/60 hover:bg-white/10'
              }`}
            >
              {f === 'pending' ? 'Pendentes' : f === 'completed' ? 'Concluídos' : 'Todos'}
            </button>
          ))}
        </div>

        {/* New Deadline Form */}
        {showForm && (
          <div className="bg-white/5 rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Novo Prazo</h2>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm text-white/60 mb-2">Descrição</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Ex: Responder contestação"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Dias</label>
                <input
                  type="number"
                  value={formData.days}
                  onChange={(e) => setFormData({ ...formData, days: parseInt(e.target.value), due_date: '' })}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Ou Data Específica</label>
                <input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value, days: 0 })}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Urgência</label>
                <select
                  value={formData.urgency}
                  onChange={(e) => setFormData({ ...formData, urgency: e.target.value })}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                >
                  <option value="low">Baixa</option>
                  <option value="medium">Média</option>
                  <option value="high">Alta</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Contexto/Processo</label>
                <input
                  type="text"
                  value={formData.context}
                  onChange={(e) => setFormData({ ...formData, context: e.target.value })}
                  placeholder="Ex: Processo 12345 - Cliente ABC"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div className="md:col-span-2 flex gap-3">
                <button
                  type="submit"
                  className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg font-semibold hover:opacity-90 transition"
                >
                  Criar Prazo
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-3 bg-white/5 hover:bg-white/10 rounded-lg transition"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Deadlines List */}
        <div className="bg-white/5 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-semibold">
              {filter === 'pending' ? 'Prazos Pendentes' : filter === 'completed' ? 'Prazos Concluídos' : 'Todos os Prazos'}
              <span className="ml-2 text-white/40 text-sm">({deadlines.length})</span>
            </h2>
          </div>

          {deadlines.length === 0 ? (
            <div className="text-center py-12 text-white/40">
              <div className="text-4xl mb-4">📅</div>
              <p>Nenhum prazo encontrado</p>
            </div>
          ) : (
            <div className="divide-y divide-white/10">
              {deadlines.map((deadline) => {
                const alert = alerts.find(a => a.deadline_id === deadline.id);
                return (
                  <div
                    key={deadline.id}
                    className={`p-4 flex items-center justify-between hover:bg-white/5 transition ${
                      deadline.is_completed ? 'opacity-50' : ''
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      {alert && !deadline.is_completed && (
                        <span className={`px-3 py-1 rounded-lg text-sm font-medium ${getAlertColor(alert.alert_level)}`}>
                          {alert.alert_message}
                        </span>
                      )}
                      {deadline.is_completed && (
                        <span className="px-3 py-1 rounded-lg text-sm bg-emerald-500/20 text-emerald-400">
                          ✓ Concluído
                        </span>
                      )}
                      <div>
                        <p className={`font-semibold ${deadline.is_completed ? 'line-through text-white/50' : ''}`}>
                          {deadline.description}
                        </p>
                        <p className="text-sm text-white/50">
                          {deadline.context} • Vence: {new Date(deadline.due_date).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 rounded-lg text-sm ${getUrgencyColor(deadline.urgency)}`}>
                        {deadline.urgency === 'high' ? 'Alta' : deadline.urgency === 'medium' ? 'Média' : 'Baixa'}
                      </span>
                      {!deadline.is_completed && (
                        <button
                          onClick={() => handleComplete(deadline.id)}
                          className="px-3 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg transition text-sm"
                        >
                          Concluir
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(deadline.id)}
                        className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition text-sm"
                      >
                        Excluir
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
