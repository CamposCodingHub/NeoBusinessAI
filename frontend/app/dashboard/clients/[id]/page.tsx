'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

interface ClientDetails {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  cpf_cnpj?: string;
  city?: string;
  state?: string;
  notes?: string;
  status?: string;
  total_billed?: number;
  outstanding_amount?: number;
  documents?: { id: number; filename: string; status: string }[];
  invoices?: { id: number; invoice_number?: string; description?: string; total?: number; status?: string }[];
}

interface TimelineEvent {
  type: string;
  date: string;
  title: string;
  description: string;
  amount?: number;
  status?: string;
}

export default function ClientDetailsPage() {
  const params = useParams<{ id: string }>();
  const [client, setClient] = useState<ClientDetails | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  const getAccessToken = () => {
    const tokenStr = localStorage.getItem('neobusiness_tokens');
    if (!tokenStr) return '';
    try {
      const token = JSON.parse(tokenStr);
      return token?.access_token || '';
    } catch {
      return '';
    }
  };

  useEffect(() => {
    const loadData = async () => {
      const accessToken = getAccessToken();
      if (!accessToken || !params?.id) {
        window.location.href = '/login';
        return;
      }

      try {
        const [detailsResponse, timelineResponse] = await Promise.all([
          fetch(`${API_URL}/clients/${params.id}`, {
            headers: { Authorization: `Bearer ${accessToken}` },
            credentials: 'omit',
          }),
          fetch(`${API_URL}/clients/${params.id}/timeline`, {
            headers: { Authorization: `Bearer ${accessToken}` },
            credentials: 'omit',
          }),
        ]);

        if (!detailsResponse.ok) {
          throw new Error('Nao foi possivel carregar os dados do cliente.');
        }

        const detailsData = await detailsResponse.json();
        setClient(detailsData);

        if (timelineResponse.ok) {
          const timelineData = await timelineResponse.json();
          setTimeline(timelineData?.events || []);
        }
      } catch (error) {
        console.error('Erro ao carregar cliente:', error);
        setErrorMessage(
          error instanceof Error ? error.message : 'Falha ao carregar o cliente.'
        );
      } finally {
        setLoading(false);
      }
    };

    void loadData();
  }, [params?.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-white p-8">
        <div className="max-w-5xl mx-auto">
          <Link href="/dashboard/clients" className="text-cyan-400 hover:text-cyan-300">
            Voltar para clientes
          </Link>
          <div className="mt-6 rounded-3xl border border-red-500/20 bg-red-500/10 p-8">
            <h1 className="text-2xl font-bold">Cliente indisponivel</h1>
            <p className="mt-3 text-white/60">
              {errorMessage || 'Nao foi possivel abrir os detalhes deste cliente.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard/clients" className="text-cyan-400 hover:text-cyan-300">
              Voltar para clientes
            </Link>
            <h1 className="mt-3 text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
              {client.name}
            </h1>
            <p className="text-white/55 mt-1">
              Visao consolidada do relacionamento, faturamento e historico.
            </p>
          </div>
          <div className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm text-white/70">
            Status: {client.status || 'ativo'}
          </div>
        </div>

        {errorMessage && (
          <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {errorMessage}
          </div>
        )}

        <div className="grid lg:grid-cols-[1.2fr_0.8fr] gap-6">
          <div className="space-y-6">
            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <h2 className="text-xl font-semibold">Dados principais</h2>
              <div className="mt-4 grid md:grid-cols-2 gap-4 text-sm">
                <div className="rounded-2xl bg-black/20 p-4">
                  <div className="text-white/40">Email</div>
                  <div className="mt-1">{client.email || '-'}</div>
                </div>
                <div className="rounded-2xl bg-black/20 p-4">
                  <div className="text-white/40">Telefone</div>
                  <div className="mt-1">{client.phone || '-'}</div>
                </div>
                <div className="rounded-2xl bg-black/20 p-4">
                  <div className="text-white/40">CPF/CNPJ</div>
                  <div className="mt-1">{client.cpf_cnpj || '-'}</div>
                </div>
                <div className="rounded-2xl bg-black/20 p-4">
                  <div className="text-white/40">Localizacao</div>
                  <div className="mt-1">
                    {client.city ? `${client.city}${client.state ? `, ${client.state}` : ''}` : '-'}
                  </div>
                </div>
              </div>
              {client.notes && (
                <div className="mt-4 rounded-2xl bg-black/20 p-4 text-sm">
                  <div className="text-white/40 mb-2">Observacoes</div>
                  <div className="text-white/75 whitespace-pre-wrap">{client.notes}</div>
                </div>
              )}
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <h2 className="text-xl font-semibold">Timeline do relacionamento</h2>
              {timeline.length === 0 ? (
                <p className="mt-4 text-white/45">Nenhum evento registrado ainda.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {timeline.map((event, index) => (
                    <div key={`${event.type}-${index}`} className="rounded-2xl bg-black/20 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-medium">{event.title}</div>
                        <div className="text-xs text-white/35">
                          {new Date(event.date).toLocaleString('pt-BR')}
                        </div>
                      </div>
                      <div className="mt-2 text-sm text-white/65">{event.description}</div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          <div className="space-y-6">
            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <h2 className="text-xl font-semibold">Resumo financeiro</h2>
              <div className="mt-4 grid gap-4">
                <div className="rounded-2xl bg-emerald-500/10 border border-emerald-500/20 p-4">
                  <div className="text-emerald-300 text-sm">Total recebido</div>
                  <div className="mt-1 text-2xl font-bold">
                    {new Intl.NumberFormat('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    }).format(client.total_billed || 0)}
                  </div>
                </div>
                <div className="rounded-2xl bg-amber-500/10 border border-amber-500/20 p-4">
                  <div className="text-amber-300 text-sm">Valor em aberto</div>
                  <div className="mt-1 text-2xl font-bold">
                    {new Intl.NumberFormat('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    }).format(client.outstanding_amount || 0)}
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <h2 className="text-xl font-semibold">Documentos vinculados</h2>
              <div className="mt-4 space-y-3">
                {(client.documents || []).length === 0 ? (
                  <p className="text-white/45">Nenhum documento vinculado.</p>
                ) : (
                  (client.documents || []).map((document) => (
                    <div key={document.id} className="rounded-2xl bg-black/20 p-4">
                      <div className="font-medium">{document.filename}</div>
                      <div className="mt-1 text-sm text-white/45">Status: {document.status}</div>
                    </div>
                  ))
                )}
              </div>
            </section>

            <section className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <h2 className="text-xl font-semibold">Faturas vinculadas</h2>
              <div className="mt-4 space-y-3">
                {(client.invoices || []).length === 0 ? (
                  <p className="text-white/45">Nenhuma fatura vinculada.</p>
                ) : (
                  (client.invoices || []).map((invoice) => (
                    <div key={invoice.id} className="rounded-2xl bg-black/20 p-4">
                      <div className="font-medium">
                        {invoice.invoice_number || `Fatura #${invoice.id}`}
                      </div>
                      <div className="mt-1 text-sm text-white/55">
                        {invoice.description || 'Sem descricao'}
                      </div>
                      <div className="mt-2 text-sm text-white/45">
                        Status: {invoice.status || 'pendente'}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
