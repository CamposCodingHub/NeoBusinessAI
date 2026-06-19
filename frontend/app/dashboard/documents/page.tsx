'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';

interface DocumentItem {
  id: number;
  filename: string;
  title?: string;
  file_type?: string;
  file_size?: number;
  status: string;
  progress?: number;
  processing_stage?: string;
  processing_message?: string;
  error_message?: string;
  processing_time_ms?: number;
  created_at?: string;
}

interface DocumentDetail extends DocumentItem {
  summary?: string;
  analysis?: string;
  content?: {
    summary?: string;
    analysis?: string;
    document_type?: string;
    process_number?: string;
    court?: string;
    parties?: Record<string, unknown>;
    deadlines?: Array<Record<string, unknown>>;
    values?: Array<Record<string, unknown>>;
    analysis_mode?: string;
    ai_analysis_used?: boolean;
  };
  metadata?: {
    pages?: number;
    text_characters?: number;
    text_truncated?: boolean;
    extraction_method?: string;
    analysis_mode?: string;
    ai_analysis_used?: boolean;
  };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const ALLOWED_EXTENSIONS = [
  '.pdf',
  '.docx',
  '.txt',
  '.rtf',
  '.jpg',
  '.jpeg',
  '.png',
  '.tif',
  '.tiff',
];
const MAX_FILE_SIZE = 50 * 1024 * 1024;
const ACTIVE_STATUSES = new Set(['queued', 'processing']);
const STATUS_PRESENTATION: Record<
  string,
  { label: string; className: string }
> = {
  uploaded: {
    label: 'Pronto para analisar',
    className: 'border-sky-400/20 bg-sky-400/10 text-sky-300',
  },
  queued: {
    label: 'Na fila',
    className: 'border-amber-400/20 bg-amber-400/10 text-amber-300',
  },
  processing: {
    label: 'Processando',
    className: 'border-cyan-400/20 bg-cyan-400/10 text-cyan-300',
  },
  completed: {
    label: 'Concluido',
    className: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
  },
  error: {
    label: 'Requer atencao',
    className: 'border-red-400/20 bg-red-400/10 text-red-300',
  },
};

export default function DocumentsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<DocumentDetail | null>(
    null
  );
  const [loadingDetailId, setLoadingDetailId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [statusMessage, setStatusMessage] = useState('');

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

  const clearMessages = () => {
    setErrorMessage('');
    setStatusMessage('');
  };

  const fetchDocuments = async (silent = false) => {
    const accessToken = getAccessToken();
    if (!accessToken) return;

    try {
      const response = await fetch(`${API_URL}/documents/`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        credentials: 'omit',
      });

      if (!response.ok) {
        throw new Error('Nao foi possivel carregar os documentos');
      }

      const data = await response.json();
      const nextDocuments = Array.isArray(data?.documents) ? data.documents : [];
      setDocuments((currentDocuments) => {
        for (const nextDocument of nextDocuments) {
          const previous = currentDocuments.find(
            (document) => document.id === nextDocument.id
          );
          if (!previous || !ACTIVE_STATUSES.has(previous.status)) continue;

          if (nextDocument.status === 'completed') {
            setErrorMessage('');
            setStatusMessage('Analise concluida e documento atualizado.');
          } else if (nextDocument.status === 'error') {
            setStatusMessage('');
            setErrorMessage(
              nextDocument.error_message
                ? `Falha na analise: ${nextDocument.error_message}`
                : 'A analise falhou. Revise o arquivo e tente novamente.'
            );
          }
        }
        return nextDocuments;
      });
    } catch (error) {
      console.error('Erro ao buscar documentos:', error);
      if (!silent) {
        setErrorMessage('Nao foi possivel carregar a lista de documentos.');
      }
    }
  };

  const validateFile = (file: File) => {
    const extension = `.${file.name.split('.').pop()?.toLowerCase() || ''}`;

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return 'Formato nao suportado. Use PDF, DOCX, TXT, RTF, JPG, PNG ou TIFF.';
    }

    if (file.size > MAX_FILE_SIZE) {
      return 'Arquivo muito grande. O limite atual e 50MB.';
    }

    return '';
  };

  const handleFileChange = (file: File | null) => {
    clearMessages();
    setSelectedFile(null);

    if (!file) return;

    const validationError = validateFile(file);
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setSelectedFile(file);
    setStatusMessage(`Arquivo selecionado: ${file.name}`);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    clearMessages();
    setUploading(true);

    try {
      const accessToken = getAccessToken();
      if (!accessToken) return;

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${API_URL}/documents/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
        credentials: 'omit',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || errorData?.error || 'Falha no upload do documento'
        );
      }

      await fetchDocuments();
      setSelectedFile(null);
      setStatusMessage('Documento enviado com sucesso.');
    } catch (error) {
      console.error('Erro no upload:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Erro no upload.');
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async (docId: number) => {
    clearMessages();
    setAnalyzingId(docId);

    try {
      const accessToken = getAccessToken();
      if (!accessToken) return;

      const response = await fetch(`${API_URL}/documents/${docId}/analyze`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        credentials: 'omit',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail ||
            errorData?.error ||
            'Nao foi possivel analisar o documento'
        );
      }

      const queued = await response.json();
      setDocuments((current) =>
        current.map((document) =>
          document.id === docId
            ? {
                ...document,
                status: queued.status || 'queued',
                progress: queued.progress || 5,
                processing_stage: 'queued',
                processing_message: 'Documento aguardando worker disponivel',
                error_message: '',
              }
            : document
        )
      );
      setStatusMessage(
        'Documento enviado para a fila. Voce pode continuar usando o sistema.'
      );
    } catch (error) {
      console.error('Erro na analise:', error);
      setErrorMessage(
        error instanceof Error && error.message
          ? `Falha na analise: ${error.message}`
          : 'Erro ao analisar documento. Verifique a conexao e tente novamente.'
      );
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!window.confirm('Deseja realmente excluir este documento?')) {
      return;
    }

    clearMessages();
    setDeletingId(docId);

    try {
      const accessToken = getAccessToken();
      if (!accessToken) return;

      const response = await fetch(`${API_URL}/documents/${docId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        credentials: 'omit',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail ||
            errorData?.error ||
            'Nao foi possivel excluir o documento'
        );
      }

      setDocuments((current) => current.filter((doc) => doc.id !== docId));
      setStatusMessage('Documento excluido com sucesso.');
    } catch (error) {
      console.error('Erro ao excluir documento:', error);
      setErrorMessage(
        error instanceof Error ? error.message : 'Erro ao excluir documento.'
      );
    } finally {
      setDeletingId(null);
    }
  };

  const handleViewResult = async (docId: number) => {
    clearMessages();
    setLoadingDetailId(docId);
    try {
      const accessToken = getAccessToken();
      if (!accessToken) return;

      const response = await fetch(`${API_URL}/documents/${docId}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        credentials: 'omit',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail ||
            errorData?.error ||
            'Nao foi possivel abrir o resultado'
        );
      }
      setSelectedDocument(await response.json());
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Erro ao abrir o resultado.'
      );
    } finally {
      setLoadingDetailId(null);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      void fetchDocuments();
    }
  }, [isAuthenticated]);

  const hasActiveDocuments = documents.some((document) =>
    ACTIVE_STATUSES.has(document.status)
  );

  useEffect(() => {
    if (!isAuthenticated || !hasActiveDocuments) return;

    const interval = window.setInterval(() => {
      void fetchDocuments(true);
    }, 1500);

    return () => window.clearInterval(interval);
  }, [isAuthenticated, hasActiveDocuments]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-2 border-white/10 border-t-cyan-400" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Acesso Restrito</h1>
          <p className="text-white/50">Faca login para acessar seus documentos</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <a
              href="/dashboard"
              className="px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg transition text-sm"
            >
              Voltar
            </a>
            <div>
              <h1 className="text-3xl font-bold mb-2">Documentos</h1>
              <p className="text-white/50">
                Analise arquivos juridicos, contabeis e fiscais sem interromper seu trabalho.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() =>
                document
                  .getElementById('upload-form')
                  ?.scrollIntoView({ behavior: 'smooth' })
              }
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 font-semibold"
            >
              Novo Documento
            </motion.button>
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

        {(errorMessage || statusMessage) && (
          <div
            className={`mb-6 rounded-xl border p-4 text-sm ${
              errorMessage
                ? 'border-red-500/30 bg-red-500/10 text-red-300'
                : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
            }`}
          >
            {errorMessage || statusMessage}
          </div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 mb-8"
        >
          <form id="upload-form" onSubmit={handleUpload} className="space-y-4">
            <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:border-cyan-500/50 transition-colors">
              <input
                type="file"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                accept=".pdf,.docx,.txt,.rtf,.jpg,.jpeg,.png,.tif,.tiff"
                className="hidden"
                id="file-input"
              />
              <label htmlFor="file-input" className="cursor-pointer">
                <div className="text-4xl mb-2">Arquivo</div>
                <p className="text-white/70 mb-2">
                  {selectedFile ? selectedFile.name : 'Clique para selecionar um documento'}
                </p>
                <p className="text-white/40 text-sm">
                  PDF, DOCX, TXT, RTF, JPG, PNG ou TIFF (max. 50MB)
                </p>
              </label>
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={!selectedFile || uploading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 font-semibold disabled:opacity-50"
            >
              {uploading ? 'Enviando...' : 'Fazer Upload'}
            </motion.button>
          </form>
        </motion.div>

        <div className="space-y-4" data-testid="documents-list">
          {documents.length === 0 ? (
            <div className="text-center py-12 text-white/50">
              <div className="text-4xl mb-4">Pasta vazia</div>
              <p>Nenhum documento ainda</p>
            </div>
          ) : (
            documents.map((doc) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="glass-card p-4 flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center text-sm font-semibold">
                    {(doc.file_type || 'doc').replace('.', '').toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold">{doc.title || doc.filename}</h3>
                    <p className="text-sm text-white/50">
                      {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : '0 KB'}
                      {' | '}
                      {(STATUS_PRESENTATION[doc.status] || STATUS_PRESENTATION.uploaded).label}
                    </p>
                    <span
                      className={`mt-2 inline-flex rounded-full border px-2.5 py-1 text-xs ${
                        (STATUS_PRESENTATION[doc.status] || STATUS_PRESENTATION.uploaded)
                          .className
                      }`}
                    >
                      {(STATUS_PRESENTATION[doc.status] || STATUS_PRESENTATION.uploaded).label}
                    </span>
                    {ACTIVE_STATUSES.has(doc.status) && (
                      <div
                        className="mt-3 w-full max-w-md"
                        data-testid={`document-progress-${doc.id}`}
                      >
                        <div className="mb-1 flex items-center justify-between gap-4 text-xs text-white/50">
                          <span>
                            {doc.processing_message || 'Preparando processamento'}
                          </span>
                          <span>{Math.max(5, doc.progress || 0)}%</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-white/10">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${Math.max(5, doc.progress || 0)}%` }}
                            className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-blue-500 to-emerald-400"
                          />
                        </div>
                      </div>
                    )}
                    {doc.status === 'error' && doc.error_message && (
                      <p className="mt-2 max-w-xl text-xs text-red-300">
                        {doc.error_message}
                      </p>
                    )}
                    {doc.status === 'completed' && doc.processing_time_ms ? (
                      <p className="mt-2 text-xs text-emerald-300/70">
                        Processado em {(doc.processing_time_ms / 1000).toFixed(1)}s
                      </p>
                    ) : null}
                    {doc.created_at && (
                      <p className="text-xs text-white/30">
                        Criado em {new Date(doc.created_at).toLocaleString('pt-BR')}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  {doc.status === 'completed' && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => void handleViewResult(doc.id)}
                      disabled={loadingDetailId === doc.id}
                      className="px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 text-sm disabled:opacity-50"
                    >
                      {loadingDetailId === doc.id ? 'Abrindo...' : 'Ver resultado'}
                    </motion.button>
                  )}
                  {['uploaded', 'error', 'completed'].includes(doc.status) && (
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => void handleAnalyze(doc.id)}
                      disabled={analyzingId === doc.id}
                      className="px-4 py-2 rounded-lg bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 text-sm disabled:opacity-50"
                    >
                      {analyzingId === doc.id
                        ? 'Enviando...'
                        : doc.status === 'error'
                        ? 'Tentar novamente'
                        : doc.status === 'completed'
                        ? 'Reanalisar'
                        : 'Analisar'}
                    </motion.button>
                  )}
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => void handleDelete(doc.id)}
                    disabled={
                      deletingId === doc.id || ACTIVE_STATUSES.has(doc.status)
                    }
                    className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 text-sm disabled:opacity-50"
                  >
                    {deletingId === doc.id ? 'Excluindo...' : 'Excluir'}
                  </motion.button>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>

      {selectedDocument && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
          data-testid="document-result-modal"
        >
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-3xl border border-white/10 bg-[#101018] p-6 shadow-2xl"
          >
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <p className="mb-2 text-xs uppercase tracking-[0.22em] text-emerald-300">
                  Resultado da analise
                </p>
                <h2 className="text-2xl font-bold">
                  {selectedDocument.title || selectedDocument.filename}
                </h2>
                <p className="mt-2 text-sm text-white/45">
                  {selectedDocument.content?.document_type || 'Documento profissional'}
                  {selectedDocument.metadata?.pages
                    ? ` | ${selectedDocument.metadata.pages} pagina(s)`
                    : ''}
                  {selectedDocument.processing_time_ms
                    ? ` | ${(selectedDocument.processing_time_ms / 1000).toFixed(1)}s`
                    : ''}
                </p>
              </div>
              <button
                onClick={() => setSelectedDocument(null)}
                className="rounded-xl border border-white/10 px-4 py-2 text-sm text-white/70 hover:bg-white/10"
              >
                Fechar
              </button>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs uppercase tracking-wider text-white/40">
                  Extracao
                </p>
                <p className="mt-2 font-semibold">
                  {selectedDocument.metadata?.extraction_method || 'Nao informado'}
                </p>
                <p className="mt-1 text-xs text-white/45">
                  {selectedDocument.metadata?.text_characters?.toLocaleString('pt-BR') ||
                    0}{' '}
                  caracteres
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs uppercase tracking-wider text-white/40">
                  Motor
                </p>
                <p className="mt-2 font-semibold">
                  {selectedDocument.metadata?.ai_analysis_used
                    ? 'IA profissional'
                    : 'Analise estruturada local'}
                </p>
                <p className="mt-1 text-xs text-white/45">
                  {selectedDocument.metadata?.analysis_mode || 'modo nao informado'}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="text-xs uppercase tracking-wider text-white/40">
                  Identificacao
                </p>
                <p className="mt-2 font-semibold">
                  {selectedDocument.content?.process_number || 'Sem numero detectado'}
                </p>
                <p className="mt-1 text-xs text-white/45">
                  {selectedDocument.content?.court || 'Orgao nao identificado'}
                </p>
              </div>
            </div>

            <section className="mt-6 rounded-2xl border border-cyan-400/15 bg-cyan-400/[0.04] p-5">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-cyan-300">
                Resumo executivo
              </h3>
              <p className="mt-3 whitespace-pre-wrap leading-7 text-white/75">
                {selectedDocument.summary ||
                  selectedDocument.content?.summary ||
                  'Resumo nao disponivel.'}
              </p>
            </section>

            <section className="mt-4 rounded-2xl border border-white/10 bg-white/[0.025] p-5">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-white/60">
                Analise profissional
              </h3>
              <div className="mt-3 whitespace-pre-wrap leading-7 text-white/75">
                {selectedDocument.analysis ||
                  selectedDocument.content?.analysis ||
                  'Analise nao disponivel.'}
              </div>
            </section>

            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              {[
                ['Partes', selectedDocument.content?.parties],
                ['Prazos', selectedDocument.content?.deadlines],
                ['Valores', selectedDocument.content?.values],
              ].map(([label, value]) => (
                <section
                  key={String(label)}
                  className="rounded-2xl border border-white/10 bg-white/[0.025] p-4"
                >
                  <h3 className="text-sm font-semibold text-white/70">{String(label)}</h3>
                  <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-white/50">
                    {JSON.stringify(value || {}, null, 2)}
                  </pre>
                </section>
              ))}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
