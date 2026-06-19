"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";
import DeadlineCalendar from "@/components/DeadlineCalendar";

// Cores LexScan
const colors = {
  primary: "#1e3a5f",
  secondary: "#c9a227",
  accent: "#10b981",
  danger: "#ef4444",
  dark: "#0f172a",
  light: "#f8fafc",
  gray: "#64748b"
};

interface Document {
  id: number;
  filename: string;
  type: string;
  process_number: string;
  parties: {
    autor?: string;
    reu?: string;
  };
  deadlines: Array<{
    days: string;
    urgency: string;
    context: string;
  }>;
  values: Array<{
    value: string;
    context: string;
  }>;
  analysis: string;
  summary: string;
  uploaded_at: string;
  status: string;
}

interface Stats {
  total_documents: number;
  total_deadlines: number;
  urgent_deadlines: number;
  document_types: Record<string, number>;
  last_upload: string | null;
}

export default function Dashboard() {
  const router = useRouter();
  const { user } = useAuth();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<Array<{role: string; text: string}>>([]);
  const [activeTab, setActiveTab] = useState<"documents" | "calendar" | "deadlines" | "upload">("documents");
  const [deadlines, setDeadlines] = useState<Array<any>>([]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Carregar estatísticas
  const loadStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/dashboard/stats`);
      const data = await res.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error("Erro ao carregar estatísticas:", error);
    }
  }, [API_URL]);

  // Carregar documentos
  const loadDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/documents`);
      const data = await res.json();
      if (data.success) {
        setDocuments(data.documents);
      }
    } catch (error) {
      console.error("Erro ao carregar documentos:", error);
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  // Carregar prazos
  const loadDeadlines = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/deadlines`);
      const data = await res.json();
      if (data.success) {
        setDeadlines(data.deadlines);
      }
    } catch (error) {
      console.error("Erro ao carregar prazos:", error);
    }
  }, [API_URL]);

  useEffect(() => {
    loadStats();
    loadDocuments();
    loadDeadlines();
  }, [loadStats, loadDocuments, loadDeadlines]);

  // Upload de documento
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/api/documents/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        setDocuments([data.document, ...documents]);
        loadStats();
        loadDeadlines();
        alert("Documento processado com sucesso!");
      } else {
        alert("Erro ao processar documento: " + data.error);
      }
    } catch (error) {
      alert("Erro ao fazer upload");
    } finally {
      setUploading(false);
    }
  };

  // Chat com documento
  const handleChat = async () => {
    if (!selectedDoc || !chatMessage.trim()) return;

    const userMessage = chatMessage.trim();
    setChatHistory([...chatHistory, { role: "user", text: userMessage }]);
    setChatMessage("");

    try {
      const res = await fetch(`${API_URL}/api/documents/${selectedDoc.id}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage }),
      });

      const data = await res.json();
      if (data.success) {
        setChatHistory(prev => [...prev, { role: "ai", text: data.answer }]);
      }
    } catch (error) {
      setChatHistory(prev => [...prev, { role: "ai", text: "Erro ao processar pergunta." }]);
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case "high": return colors.danger;
      case "medium": return colors.secondary;
      default: return colors.accent;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  return (
    <ProtectedRoute>
      <div className="dashboard" style={{ display: "flex", minHeight: "100vh", background: colors.dark }}>
        {/* Sidebar */}
        <Sidebar />

        {/* Main Content */}
        <main className="main-content" style={{ flex: 1, marginLeft: "260px", padding: "32px" }}>
          {/* Header */}
          <div className="header" style={{ marginBottom: "32px" }}>
            <h1 style={{ color: colors.light, fontSize: "28px", marginBottom: "8px" }}>
              ⚖️ Dashboard LexScan
            </h1>
            <p style={{ color: colors.gray }}>
              Bem-vindo, {user?.email || "Advogado"} | Gerencie seus documentos e prazos
            </p>
          </div>

          {/* Stats Cards */}
          <div className="stats-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "20px", marginBottom: "32px" }}>
            <div className="stat-card" style={{ background: `${colors.primary}30`, border: `1px solid ${colors.primary}50`, borderRadius: "12px", padding: "24px" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>📄</div>
              <div style={{ color: colors.gray, fontSize: "14px" }}>Documentos</div>
              <div style={{ color: colors.light, fontSize: "28px", fontWeight: 700 }}>
                {stats?.total_documents || 0}
              </div>
            </div>
            <div className="stat-card" style={{ background: `${colors.primary}30`, border: `1px solid ${colors.primary}50`, borderRadius: "12px", padding: "24px" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>⏰</div>
              <div style={{ color: colors.gray, fontSize: "14px" }}>Prazos Totais</div>
              <div style={{ color: colors.light, fontSize: "28px", fontWeight: 700 }}>
                {stats?.total_deadlines || 0}
              </div>
            </div>
            <div className="stat-card" style={{ background: `${colors.danger}20`, border: `1px solid ${colors.danger}50`, borderRadius: "12px", padding: "24px" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>🚨</div>
              <div style={{ color: colors.gray, fontSize: "14px" }}>Prazos Urgentes</div>
              <div style={{ color: colors.danger, fontSize: "28px", fontWeight: 700 }}>
                {stats?.urgent_deadlines || 0}
              </div>
            </div>
            <div className="stat-card" style={{ background: `${colors.accent}20`, border: `1px solid ${colors.accent}50`, borderRadius: "12px", padding: "24px" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>✅</div>
              <div style={{ color: colors.gray, fontSize: "14px" }}>Processados Hoje</div>
              <div style={{ color: colors.accent, fontSize: "28px", fontWeight: 700 }}>
                {documents.filter(d => d.uploaded_at?.includes(new Date().toISOString().split('T')[0])).length}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="tabs" style={{ display: "flex", gap: "8px", marginBottom: "24px", borderBottom: `1px solid ${colors.primary}30`, paddingBottom: "16px" }}>
            {[
              { id: "documents", label: "📄 Documentos", icon: "📄" },
              { id: "calendar", label: "📅 Calendário", icon: "📅" },
              { id: "deadlines", label: "⏰ Prazos", icon: "⏰" },
              { id: "upload", label: "📤 Upload", icon: "📤" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  padding: "12px 24px",
                  borderRadius: "8px",
                  border: "none",
                  background: activeTab === tab.id ? colors.secondary : "transparent",
                  color: activeTab === tab.id ? colors.dark : colors.light,
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content Area */}
          <div className="content-area" style={{ minHeight: "500px" }}>
            {/* DOCUMENTS TAB */}
            {activeTab === "documents" && (
              <div>
                <h2 style={{ color: colors.light, marginBottom: "20px" }}>Documentos Processados</h2>
                {loading ? (
                  <div style={{ color: colors.gray, textAlign: "center", padding: "40px" }}>Carregando...</div>
                ) : documents.length === 0 ? (
                  <div style={{ color: colors.gray, textAlign: "center", padding: "40px" }}>
                    Nenhum documento ainda. Faça upload na aba "Upload".
                  </div>
                ) : (
                  <div style={{ display: "grid", gap: "16px" }}>
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        onClick={() => setSelectedDoc(doc)}
                        style={{
                          background: `${colors.primary}20`,
                          border: `1px solid ${selectedDoc?.id === doc.id ? colors.secondary : colors.primary}40`,
                          borderRadius: "12px",
                          padding: "20px",
                          cursor: "pointer",
                          transition: "all 0.2s",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div>
                            <div style={{ color: colors.light, fontWeight: 600, marginBottom: "4px" }}>
                              {doc.filename}
                            </div>
                            <div style={{ color: colors.gray, fontSize: "14px" }}>
                              {doc.type} • {formatDate(doc.uploaded_at)}
                            </div>
                          </div>
                          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                            {doc.deadlines?.length > 0 && (
                              <span style={{
                                background: `${colors.danger}20`,
                                color: colors.danger,
                                padding: "4px 12px",
                                borderRadius: "20px",
                                fontSize: "12px"
                              }}>
                                {doc.deadlines.length} prazo(s)
                              </span>
                            )}
                            <span style={{ fontSize: "20px" }}>📄</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Document Detail Modal */}
                {selectedDoc && (
                  <div style={{
                    position: "fixed",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: "rgba(0,0,0,0.8)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    zIndex: 1000,
                    padding: "20px"
                  }}>
                    <div style={{
                      background: colors.dark,
                      border: `1px solid ${colors.primary}50`,
                      borderRadius: "16px",
                      width: "100%",
                      maxWidth: "900px",
                      maxHeight: "90vh",
                      overflow: "auto",
                      padding: "32px"
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
                        <h2 style={{ color: colors.light }}>{selectedDoc.filename}</h2>
                        <button
                          onClick={() => setSelectedDoc(null)}
                          style={{ background: "transparent", border: "none", color: colors.light, fontSize: "24px", cursor: "pointer" }}
                        >
                          ×
                        </button>
                      </div>

                      <div style={{ display: "grid", gap: "16px", marginBottom: "24px" }}>
                        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
                          <div style={{ background: `${colors.primary}30`, padding: "12px 16px", borderRadius: "8px" }}>
                            <div style={{ color: colors.gray, fontSize: "12px" }}>Tipo</div>
                            <div style={{ color: colors.light }}>{selectedDoc.type}</div>
                          </div>
                          <div style={{ background: `${colors.primary}30`, padding: "12px 16px", borderRadius: "8px" }}>
                            <div style={{ color: colors.gray, fontSize: "12px" }}>Processo</div>
                            <div style={{ color: colors.light }}>{selectedDoc.process_number || "N/A"}</div>
                          </div>
                          <div style={{ background: `${colors.primary}30`, padding: "12px 16px", borderRadius: "8px" }}>
                            <div style={{ color: colors.gray, fontSize: "12px" }}>Data</div>
                            <div style={{ color: colors.light }}>{formatDate(selectedDoc.uploaded_at)}</div>
                          </div>
                        </div>

                        {/* Partes */}
                        {(selectedDoc.parties?.autor || selectedDoc.parties?.reu) && (
                          <div style={{ background: `${colors.primary}20`, padding: "16px", borderRadius: "8px" }}>
                            <h4 style={{ color: colors.secondary, marginBottom: "8px" }}>👥 Partes</h4>
                            {selectedDoc.parties.autor && <div style={{ color: colors.light }}>Autor: {selectedDoc.parties.autor}</div>}
                            {selectedDoc.parties.reu && <div style={{ color: colors.light }}>Réu: {selectedDoc.parties.reu}</div>}
                          </div>
                        )}

                        {/* Prazos */}
                        {selectedDoc.deadlines?.length > 0 && (
                          <div style={{ background: `${colors.danger}10`, padding: "16px", borderRadius: "8px", border: `1px solid ${colors.danger}30` }}>
                            <h4 style={{ color: colors.danger, marginBottom: "8px" }}>⏰ Prazos Identificados</h4>
                            {selectedDoc.deadlines.map((dl, idx) => (
                              <div key={idx} style={{
                                color: colors.light,
                                marginBottom: "4px",
                                padding: "8px",
                                background: `${getUrgencyColor(dl.urgency)}20`,
                                borderRadius: "4px"
                              }}>
                                <strong>{dl.days} dias</strong> - {dl.context?.substring(0, 100)}...
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Análise */}
                        {selectedDoc.analysis && (
                          <div style={{ background: `${colors.accent}10`, padding: "16px", borderRadius: "8px" }}>
                            <h4 style={{ color: colors.accent, marginBottom: "8px" }}>🤖 Análise da IA</h4>
                            <div style={{ color: colors.light, whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                              {selectedDoc.analysis}
                            </div>
                          </div>
                        )}

                        {/* Chat */}
                        <div style={{ border: `1px solid ${colors.primary}50`, borderRadius: "8px", padding: "16px" }}>
                          <h4 style={{ color: colors.secondary, marginBottom: "12px" }}>💬 Pergunte sobre o documento</h4>
                          <div style={{ maxHeight: "200px", overflow: "auto", marginBottom: "12px" }}>
                            {chatHistory.map((msg, idx) => (
                              <div key={idx} style={{
                                marginBottom: "8px",
                                padding: "8px 12px",
                                borderRadius: "8px",
                                background: msg.role === "user" ? `${colors.primary}30` : `${colors.accent}20`,
                                color: colors.light
                              }}>
                                <strong>{msg.role === "user" ? "Você: " : "LexScan: "}</strong>
                                {msg.text}
                              </div>
                            ))}
                          </div>
                          <div style={{ display: "flex", gap: "8px" }}>
                            <input
                              type="text"
                              value={chatMessage}
                              onChange={(e) => setChatMessage(e.target.value)}
                              onKeyDown={(e) => e.key === "Enter" && handleChat()}
                              placeholder="Ex: Qual o prazo para contestação?"
                              style={{
                                flex: 1,
                                padding: "12px",
                                borderRadius: "8px",
                                border: `1px solid ${colors.primary}50`,
                                background: colors.dark,
                                color: colors.light
                              }}
                            />
                            <button
                              onClick={handleChat}
                              style={{
                                padding: "12px 24px",
                                background: colors.secondary,
                                color: colors.dark,
                                border: "none",
                                borderRadius: "8px",
                                cursor: "pointer",
                                fontWeight: 600
                              }}
                            >
                              Enviar
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* CALENDAR TAB */}
            {activeTab === "calendar" && (
              <div>
                <h2 style={{ color: colors.light, marginBottom: "20px" }}>📅 Calendário de Prazos</h2>
                <DeadlineCalendar deadlines={deadlines} />
              </div>
            )}

            {/* DEADLINES TAB */}
            {activeTab === "deadlines" && (
              <div>
                <h2 style={{ color: colors.light, marginBottom: "20px" }}>⏰ Lista de Prazos</h2>
                {deadlines.length === 0 ? (
                  <div style={{ color: colors.gray, textAlign: "center", padding: "40px" }}>
                    Nenhum prazo identificado ainda.
                  </div>
                ) : (
                  <div style={{ display: "grid", gap: "12px" }}>
                    {deadlines.map((dl, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: `${getUrgencyColor(dl.urgency)}20`,
                          border: `1px solid ${getUrgencyColor(dl.urgency)}50`,
                          borderRadius: "12px",
                          padding: "16px 20px",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center"
                        }}
                      >
                        <div>
                          <div style={{ color: colors.light, fontWeight: 600, marginBottom: "4px" }}>
                            {dl.deadline.days} dias
                          </div>
                          <div style={{ color: colors.gray, fontSize: "14px" }}>
                            {dl.document_name} • {dl.document_type}
                          </div>
                          {dl.process_number && (
                            <div style={{ color: colors.secondary, fontSize: "12px" }}>
                              Processo: {dl.process_number}
                            </div>
                          )}
                        </div>
                        <div style={{
                          background: getUrgencyColor(dl.urgency),
                          color: colors.dark,
                          padding: "6px 16px",
                          borderRadius: "20px",
                          fontSize: "12px",
                          fontWeight: 600,
                          textTransform: "uppercase"
                        }}>
                          {dl.urgency === "high" ? "🔥 Urgente" : dl.urgency === "medium" ? "⚠️ Médio" : "✅ Baixo"}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* UPLOAD TAB */}
            {activeTab === "upload" && (
              <div>
                <h2 style={{ color: colors.light, marginBottom: "20px" }}>📤 Upload de Documento</h2>
                <div
                  style={{
                    border: `2px dashed ${colors.primary}50`,
                    borderRadius: "16px",
                    padding: "60px 40px",
                    textAlign: "center",
                    background: `${colors.primary}10`
                  }}
                >
                  <div style={{ fontSize: "64px", marginBottom: "16px" }}>📄</div>
                  <h3 style={{ color: colors.light, marginBottom: "8px" }}>Arraste seu documento aqui</h3>
                  <p style={{ color: colors.gray, marginBottom: "24px" }}>
                    Ou clique para selecionar PDF, JPG, PNG
                  </p>
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png,.tiff"
                    onChange={handleFileUpload}
                    style={{ display: "none" }}
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    style={{
                      display: "inline-block",
                      padding: "16px 32px",
                      background: colors.secondary,
                      color: colors.dark,
                      borderRadius: "8px",
                      cursor: "pointer",
                      fontWeight: 600,
                      opacity: uploading ? 0.5 : 1
                    }}
                  >
                    {uploading ? "⏳ Processando..." : "📤 Selecionar Arquivo"}
                  </label>
                  <div style={{ marginTop: "24px", color: colors.gray, fontSize: "14px" }}>
                    Formatos suportados: PDF, JPG, PNG, TIFF
                  </div>
                </div>

                <div style={{ marginTop: "32px", background: `${colors.primary}20`, padding: "24px", borderRadius: "12px" }}>
                  <h4 style={{ color: colors.secondary, marginBottom: "12px" }}>💡 O que acontece após o upload?</h4>
                  <ul style={{ color: colors.light, lineHeight: 1.8, paddingLeft: "20px" }}>
                    <li>OCR extrai o texto automaticamente</li>
                    <li>IA analisa e classifica o documento</li>
                    <li>Prazos são detectados e adicionados ao calendário</li>
                    <li>Resumo executivo é gerado</li>
                    <li>Você recebe notificações de prazos urgentes</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
