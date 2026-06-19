'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';

export default function LegalPage() {
  const { user } = useAuth();
  const [pieces, setPieces] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [formData, setFormData] = useState({
    document_id: '',
    parties: '',
    facts: '',
    requests: '',
    additional_context: ''
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const formatPieceType = (value: string) =>
    value
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (character) => character.toUpperCase());

  // Verificar autenticação diretamente do localStorage
  const isAuthenticated = typeof window !== 'undefined' && !!localStorage.getItem('neobusiness_tokens');

  const fetchPieces = async () => {
    try {
      const tokenStr = localStorage.getItem('neobusiness_tokens');
      if (!tokenStr) return;

      const token = JSON.parse(tokenStr);
      if (!token?.access_token) return;

      const response = await fetch(`${API_URL}/legal/pieces`, {
        headers: {
          'Authorization': `Bearer ${token.access_token}`,
        },
        credentials: 'omit',
      });
      if (response.ok) {
        const data = await response.json();
        setPieces(data);
      }
    } catch (error) {
      console.error('Erro ao buscar peças:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const tokenStr = localStorage.getItem('neobusiness_tokens');
      if (!tokenStr) return;

      const token = JSON.parse(tokenStr);
      if (!token?.access_token) return;

      const response = await fetch(`${API_URL}/legal/templates`, {
        headers: {
          'Authorization': `Bearer ${token.access_token}`,
        },
        credentials: 'omit',
      });
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (error) {
      console.error('Erro ao buscar templates:', error);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setGenerationError('');

    try {
      const tokenStr = localStorage.getItem('neobusiness_tokens');
      if (!tokenStr) return;

      const token = JSON.parse(tokenStr);
      if (!token?.access_token) return;

      const response = await fetch(`${API_URL}/legal/generate-piece`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token.access_token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'omit',
        body: JSON.stringify({
          ...formData,
          document_id: formData.document_id || null,
          piece_type: selectedTemplate,
          jurisdiction: 'civel' // Padrão para demo
        }),
      });

      if (response.ok) {
        const data = await response.json();
        await fetchPieces();
        setFormData({
          document_id: '',
          parties: '',
          facts: '',
          requests: '',
          additional_context: ''
        });
        setSelectedTemplate('');
      } else {
        const errorPayload = await response.json().catch(() => null);
        setGenerationError(
          typeof errorPayload?.detail === 'string'
            ? errorPayload.detail
            : 'Nao foi possivel gerar a peca. Revise os campos e tente novamente.'
        );
      }
    } catch (error) {
      console.error('Erro na geração:', error);
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchPieces();
      fetchTemplates();
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Acesso Restrito</h1>
          <p className="text-white/50">Faça login para acessar o gerador de peças</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <a href="/dashboard" className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition text-sm">
              ← Voltar
            </a>
            <div>
              <h1 className="text-3xl font-bold mb-2">Gerador de Peças Jurídicas</h1>
              <p className="text-white/50">Gere petições, contestações e recursos com IA</p>
            </div>
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6"
            >
              <h2 className="text-xl font-bold mb-6">Nova Peça</h2>

              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Tipo de Peça *</label>
                  <select
                    value={selectedTemplate}
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    required
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-cyan-500/50"
                  >
                    <option value="">Selecione o tipo...</option>
                    {templates.map((tpl: any) => (
                      <option key={tpl.id} value={tpl.id}>{tpl.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Partes Envolvidas *</label>
                  <textarea
                    value={formData.parties}
                    onChange={(e) => setFormData({...formData, parties: e.target.value})}
                    required
                    rows={2}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Ex: João Silva vs Empresa XYZ"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Fatos Relevantes *</label>
                  <textarea
                    value={formData.facts}
                    onChange={(e) => setFormData({...formData, facts: e.target.value})}
                    required
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Descreva os fatos do caso..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Pedidos *</label>
                  <textarea
                    value={formData.requests}
                    onChange={(e) => setFormData({...formData, requests: e.target.value})}
                    required
                    rows={2}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Descreva os pedidos à autoridade..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">Contexto Adicional</label>
                  <textarea
                    value={formData.additional_context}
                    onChange={(e) => setFormData({...formData, additional_context: e.target.value})}
                    rows={2}
                    className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
                    placeholder="Informações adicionais importantes..."
                  />
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  type="submit"
                  disabled={generating || !selectedTemplate}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 font-semibold disabled:opacity-50"
                >
                  {generating ? 'Gerando...' : 'Gerar Peça'}
                </motion.button>
                {generationError && (
                  <p
                    role="alert"
                    className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
                  >
                    {generationError}
                  </p>
                )}
              </form>
            </motion.div>
          </div>

          {/* Lista de Peças */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6"
            >
              <h2 className="text-xl font-bold mb-6">Peças Geradas</h2>

              {pieces.length === 0 ? (
                <div className="text-center py-12 text-white/50">
                  <div className="text-4xl mb-4">⚖️</div>
                  <p>Nenhuma peça gerada ainda</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {pieces.map((piece: any) => (
                    <motion.div
                      key={piece.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-4 rounded-xl bg-white/5 border border-white/10"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold">
                            {formatPieceType(piece.piece_type)}
                          </h3>
                          <p className="text-sm text-white/50">{piece.jurisdiction}</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          piece.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {piece.status}
                        </span>
                      </div>
                      <p className="text-sm text-white/70 line-clamp-2">
                        {piece.content
                          ? `${piece.content.substring(0, 150)}...`
                          : 'Conteudo salvo. Abra a peca pela API para revisao integral.'}
                      </p>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
