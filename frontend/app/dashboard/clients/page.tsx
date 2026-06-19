'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Client {
  id: number;
  name: string;
  email: string;
  phone: string;
  cpf_cnpj: string;
  city: string;
  state: string;
  status: 'active' | 'inactive' | 'prospect';
  created_at: string;
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive' | 'prospect'>('all');

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    cpf_cnpj: '',
    address: '',
    city: '',
    state: '',
    notes: ''
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
    fetchClients();
  }, [filter, search]);

  const fetchClients = async () => {
    const token = getToken();
    if (!token) return;

    let url = `${API_URL}/clients/?`;
    if (filter !== 'all') url += `status=${filter}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;

    try {
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (response.ok) {
        const data = await response.json();
        setClients(data.clients || []);
      }
    } catch (error) {
      console.error('Erro ao buscar clientes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();

    try {
      const response = await fetch(`${API_URL}/clients/`, {
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
        setFormData({ name: '', email: '', phone: '', cpf_cnpj: '', address: '', city: '', state: '', notes: '' });
        fetchClients();
      }
    } catch (error) {
      console.error('Erro ao criar cliente:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja excluir este cliente?')) return;

    const token = getToken();
    try {
      const response = await fetch(`${API_URL}/clients/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
        credentials: 'omit'
      });
      if (response.ok) fetchClients();
    } catch (error) {
      console.error('Erro ao excluir:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-emerald-500/20 text-emerald-400';
      case 'prospect': return 'bg-amber-500/20 text-amber-400';
      default: return 'bg-white/10 text-white/60';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Ativo';
      case 'prospect': return 'Prospecto';
      case 'inactive': return 'Inativo';
      default: return status;
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
                Gestão de Clientes
              </h1>
              <p className="text-white/60">Cadastro e histórico de clientes</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowForm(!showForm)}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-xl font-semibold hover:opacity-90 transition"
            >
              + Novo Cliente
            </button>
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

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <input
            type="text"
            placeholder="Buscar cliente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50 w-64"
          />
          <div className="flex gap-2">
            {(['all', 'active', 'prospect', 'inactive'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded-lg transition ${
                  filter === f
                    ? 'bg-cyan-500/30 text-cyan-400 border border-cyan-500/50'
                    : 'bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                {f === 'all' ? 'Todos' : f === 'active' ? 'Ativos' : f === 'prospect' ? 'Prospectos' : 'Inativos'}
              </button>
            ))}
          </div>
        </div>

        {/* New Client Form */}
        {showForm && (
          <div className="bg-white/5 rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Novo Cliente</h2>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-white/60 mb-2">Nome *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Telefone</label>
                <input
                  type="text"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">CPF/CNPJ</label>
                <input
                  type="text"
                  value={formData.cpf_cnpj}
                  onChange={(e) => setFormData({ ...formData, cpf_cnpj: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm text-white/60 mb-2">Endereço</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Cidade</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Estado</label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm text-white/60 mb-2">Observações</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-cyan-500/50"
                />
              </div>
              <div className="md:col-span-2 flex gap-3">
                <button
                  type="submit"
                  className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg font-semibold hover:opacity-90 transition"
                >
                  Criar Cliente
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Clients Table */}
        <div className="bg-white/5 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-xl font-semibold">
              Clientes <span className="text-white/40 text-sm">({clients.length})</span>
            </h2>
          </div>

          {clients.length === 0 ? (
            <div className="text-center py-12 text-white/40">
              <div className="text-4xl mb-4">👥</div>
              <p>Nenhum cliente encontrado</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5">
                  <tr>
                    <th className="text-left p-4 text-white/60 font-medium">Nome</th>
                    <th className="text-left p-4 text-white/60 font-medium">Contato</th>
                    <th className="text-left p-4 text-white/60 font-medium">Localização</th>
                    <th className="text-left p-4 text-white/60 font-medium">Status</th>
                    <th className="text-left p-4 text-white/60 font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {clients.map((client) => (
                    <tr key={client.id} className="hover:bg-white/5">
                      <td className="p-4">
                        <p className="font-medium">{client.name}</p>
                        <p className="text-sm text-white/40">{client.cpf_cnpj}</p>
                      </td>
                      <td className="p-4">
                        <p>{client.email || '-'}</p>
                        <p className="text-sm text-white/40">{client.phone || '-'}</p>
                      </td>
                      <td className="p-4 text-white/60">
                        {client.city ? `${client.city}, ${client.state}` : '-'}
                      </td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-lg text-sm ${getStatusColor(client.status)}`}>
                          {getStatusLabel(client.status)}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <Link
                            href={`/dashboard/clients/${client.id}`}
                            className="px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded-lg transition text-sm"
                          >
                            Detalhes
                          </Link>
                          <button
                            onClick={() => handleDelete(client.id)}
                            className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition text-sm"
                          >
                            Excluir
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
