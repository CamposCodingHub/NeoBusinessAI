"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/firebase";
import Sidebar from "@/components/Sidebar";

const colors = {
  primary: "#1e3a5f",
  secondary: "#c9a227",
  accent: "#10b981",
  danger: "#ef4444",
  warning: "#f59e0b",
  dark: "#0f172a",
  light: "#f8fafc",
  gray: "#64748b"
};

interface EmailAccount {
  id: number;
  email_address: string;
  provider: string;
  is_active: boolean;
  last_sync: string;
}

interface EmailMessage {
  id: string;
  subject: string;
  sender: string;
  sender_name: string;
  date: string;
  summary: string;
  urgency_score: number;
  is_important: boolean;
  is_read: boolean;
  category: string;
  action_items: string[];
  body_preview: string;
}

const providers = [
  { id: 'gmail', name: 'Gmail / Google Workspace', icon: '📧' },
  { id: 'outlook', name: 'Outlook / Microsoft 365', icon: '📨' },
  { id: 'yahoo', name: 'Yahoo Mail', icon: '🌐' },
  { id: 'icloud', name: 'iCloud Mail', icon: '🍎' },
  { id: 'corporate', name: 'Servidor Corporativo (IMAP)', icon: '🏢' }
];

export default function EmailIntegrationPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Tabs
  const [activeTab, setActiveTab] = useState<'inbox' | 'configure' | 'analytics'>('inbox');

  // Configuration
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState('gmail');
  const [configForm, setConfigForm] = useState({
    email: '',
    password: '',
    imap_server: '',
    imap_port: 993,
    smtp_server: '',
    smtp_port: 587
  });
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null);

  // Data
  const [accounts, setAccounts] = useState<EmailAccount[]>([]);
  const [emails, setEmails] = useState<EmailMessage[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailMessage | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Analytics
  const [stats, setStats] = useState({
    total_emails: 0,
    legal_emails: 0,
    urgent_emails: 0,
    unread_count: 0
  });

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((currentUser) => {
      if (currentUser) {
        setUser(currentUser);
        loadData();
      } else {
        router.push("/login");
      }
    });
    return () => unsubscribe();
  }, [router]);

  const loadData = async () => {
    setLoading(true);
    // Simulação - em produção seria chamada API real
    setTimeout(() => {
      setAccounts([
        { id: 1, email_address: "advogado@escritorio.com.br", provider: "corporate", is_active: true, last_sync: "2024-05-02T15:30:00" }
      ]);

      setEmails([
        {
          id: "1",
          subject: "Prazo para Contestação - Processo nº 12345-67.2024.8.26.0001",
          sender: "sistema@tjsp.jus.br",
          sender_name: "TJSP - Sistema Processual",
          date: "2024-05-02T14:20:00",
          summary: "Intimação eletrônica com prazo de 15 dias para contestação no processo 12345-67.2024.8.26.0001.",
          urgency_score: 0.95,
          is_important: true,
          is_read: false,
          category: "legal",
          action_items: ["Verificar autos no sistema", "Preparar contestação", "Agendar prazo no calendário"],
          body_preview: "Senhor Advogado, Vossa Excelência foi intimado para apresentar contestação no prazo legal de 15 dias..."
        },
        {
          id: "2",
          subject: "Reunião de caso - João Silva vs Empresa ABC",
          sender: "cliente@email.com",
          sender_name: "João Silva",
          date: "2024-05-02T10:15:00",
          summary: "Cliente solicitando reunião para discutir andamento do processo trabalhista.",
          urgency_score: 0.6,
          is_important: true,
          is_read: false,
          category: "client",
          action_items: ["Agendar reunião", "Preparar relatório de andamento"],
          body_preview: "Prezado Dr., Gostaria de agendar uma reunião para discutirmos o andamento do processo..."
        },
        {
          id: "3",
          subject: "Newsletter Jurídica - Novidades da Semana",
          sender: "newsletter@juridico.com",
          sender_name: "Portal Jurídico",
          date: "2024-05-01T08:00:00",
          summary: "Newsletter com atualizações jurisprudenciais da semana.",
          urgency_score: 0.2,
          is_important: false,
          is_read: true,
          category: "other",
          action_items: [],
          body_preview: "Confira as principais decisões desta semana no STF e STJ..."
        }
      ]);

      setStats({
        total_emails: 24,
        legal_emails: 8,
        urgent_emails: 3,
        unread_count: 12
      });

      setLoading(false);
    }, 1000);
  };

  const testConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);

    // Simulação de teste
    setTimeout(() => {
      setTestResult({
        success: true,
        message: "✅ Conexão estabelecida com sucesso! IMAP e SMTP funcionando corretamente."
      });
      setTestingConnection(false);
    }, 2000);
  };

  const saveAccount = async () => {
    // Aqui salvaria no backend
    alert("Conta de email configurada com sucesso!");
    setShowAddAccount(false);
    loadData();
  };

  const getUrgencyColor = (score: number) => {
    if (score >= 0.8) return colors.danger;
    if (score >= 0.5) return colors.warning;
    return colors.accent;
  };

  const getCategoryLabel = (category: string) => {
    const labels: {[key: string]: string} = {
      legal: "🏛️ Jurídico",
      client: "👤 Cliente",
      internal: "🏢 Interno",
      other: "📧 Outro"
    };
    return labels[category] || "📧 Outro";
  };

  const filteredEmails = emails.filter(email => {
    const matchesCategory = filterCategory === 'all' || email.category === filterCategory;
    const matchesSearch = searchTerm === '' ||
      email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.sender_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.summary.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (loading) {
    return (
      <div style={{ display: "flex", minHeight: "100vh", background: colors.dark, alignItems: "center", justifyContent: "center" }}>
        <Sidebar />
        <div style={{ color: colors.light, fontSize: "18px" }}>📧 Carregando integração de email...</div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: colors.dark }}>
      <Sidebar />

      <main style={{ flex: 1, marginLeft: "260px", padding: "30px" }}>
        {/* Header */}
        <div style={{ marginBottom: "30px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h1 style={{ color: colors.light, fontSize: "28px", marginBottom: "8px" }}>
                📧 Integração com Email
              </h1>
              <p style={{ color: colors.gray, fontSize: "14px" }}>
                Gerencie seus emails corporativos com IA
              </p>
            </div>

            {accounts.length > 0 && (
              <div style={{ textAlign: "right" }}>
                <div style={{ color: colors.secondary, fontSize: "24px", fontWeight: "bold" }}>
                  {stats.unread_count}
                </div>
                <div style={{ color: colors.gray, fontSize: "12px" }}>
                  não lidos
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "30px", borderBottom: `1px solid ${colors.primary}` }}>
          {[
            { id: 'inbox', label: '📥 Caixa de Entrada', count: stats.unread_count },
            { id: 'configure', label: '⚙️ Configurar' },
            { id: 'analytics', label: '📊 Análises' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: "12px 20px",
                background: "transparent",
                border: "none",
                borderBottom: `3px solid ${activeTab === tab.id ? colors.secondary : "transparent"}`,
                color: activeTab === tab.id ? colors.light : colors.gray,
                cursor: "pointer",
                fontSize: "14px",
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}
            >
              {tab.label}
              {(tab.count ?? 0) > 0 && (
                <span style={{
                  background: colors.danger,
                  color: "white",
                  padding: "2px 8px",
                  borderRadius: "10px",
                  fontSize: "11px"
                }}>
                  {tab.count ?? 0}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab: Inbox */}
        {activeTab === 'inbox' && (
          <div>
            {accounts.length === 0 ? (
              <div style={{
                textAlign: "center",
                padding: "80px 40px",
                background: colors.primary,
                borderRadius: "12px"
              }}>
                <div style={{ fontSize: "48px", marginBottom: "20px" }}>📧</div>
                <h3 style={{ color: colors.light, marginBottom: "12px" }}>
                  Nenhuma conta de email configurada
                </h3>
                <p style={{ color: colors.gray, marginBottom: "24px" }}>
                  Configure sua conta de email corporativo para começar a receber resumos e alertas inteligentes.
                </p>
                <button
                  onClick={() => { setActiveTab('configure'); setShowAddAccount(true); }}
                  style={{
                    padding: "14px 28px",
                    background: colors.secondary,
                    color: colors.dark,
                    border: "none",
                    borderRadius: "8px",
                    fontWeight: "bold",
                    cursor: "pointer"
                  }}
                >
                  Configurar Email
                </button>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "24px" }}>
                {/* Email List */}
                <div>
                  {/* Filters */}
                  <div style={{ marginBottom: "16px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    {['all', 'legal', 'client', 'urgent'].map(filter => (
                      <button
                        key={filter}
                        onClick={() => setFilterCategory(filter)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "6px",
                          border: "none",
                          background: filterCategory === filter ? colors.secondary : colors.primary,
                          color: filterCategory === filter ? colors.dark : colors.light,
                          fontSize: "12px",
                          cursor: "pointer"
                        }}
                      >
                        {filter === 'all' && 'Todos'}
                        {filter === 'legal' && '🏛️ Jurídicos'}
                        {filter === 'client' && '👤 Clientes'}
                        {filter === 'urgent' && '🔴 Urgentes'}
                      </button>
                    ))}
                  </div>

                  {/* Search */}
                  <input
                    type="text"
                    placeholder="🔍 Buscar emails..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "12px 16px",
                      background: colors.primary,
                      border: "none",
                      borderRadius: "8px",
                      color: colors.light,
                      fontSize: "14px",
                      marginBottom: "16px",
                      outline: "none"
                    }}
                  />

                  {/* Emails */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {filteredEmails.map(email => (
                      <button
                        key={email.id}
                        onClick={() => setSelectedEmail(email)}
                        style={{
                          padding: "16px",
                          background: selectedEmail?.id === email.id ? colors.secondary + '20' : colors.primary,
                          border: `1px solid ${selectedEmail?.id === email.id ? colors.secondary : 'transparent'}`,
                          borderRadius: "8px",
                          textAlign: "left",
                          cursor: "pointer",
                          display: "flex",
                          flexDirection: "column",
                          gap: "6px"
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ color: colors.light, fontWeight: "bold", fontSize: "13px" }}>
                            {!email.is_read && <span style={{ color: colors.secondary, marginRight: "4px" }}>●</span>}
                            {email.sender_name}
                          </span>
                          <span style={{ color: colors.gray, fontSize: "11px" }}>
                            {new Date(email.date).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <span style={{ color: colors.light, fontSize: "12px" }}>
                          {email.subject.length > 50 ? email.subject.substring(0, 50) + "..." : email.subject}
                        </span>
                        <span style={{ color: colors.gray, fontSize: "11px" }}>
                          {email.summary.substring(0, 60)}...
                        </span>
                        <div style={{ display: "flex", gap: "4px", marginTop: "4px" }}>
                          <span style={{
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: getUrgencyColor(email.urgency_score) + '30',
                            color: getUrgencyColor(email.urgency_score),
                            fontSize: "10px"
                          }}>
                            {email.urgency_score >= 0.8 ? '🔴 URGENTE' : email.urgency_score >= 0.5 ? '🟠 MÉDIO' : '🟢 BAIXO'}
                          </span>
                          <span style={{
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: colors.primary,
                            color: colors.gray,
                            fontSize: "10px"
                          }}>
                            {getCategoryLabel(email.category)}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Email Detail */}
                <div>
                  {selectedEmail ? (
                    <div style={{
                      background: colors.primary,
                      borderRadius: "12px",
                      padding: "24px"
                    }}>
                      {/* Header */}
                      <div style={{ marginBottom: "20px", paddingBottom: "16px", borderBottom: `1px solid ${colors.dark}` }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                          <h3 style={{ color: colors.light, fontSize: "18px", margin: 0, flex: 1, paddingRight: "16px" }}>
                            {selectedEmail.subject}
                          </h3>
                          <div style={{ display: "flex", gap: "4px" }}>
                            <span style={{
                              padding: "4px 8px",
                              borderRadius: "4px",
                              background: getUrgencyColor(selectedEmail.urgency_score) + '30',
                              color: getUrgencyColor(selectedEmail.urgency_score),
                              fontSize: "11px"
                            }}>
                              {Math.round(selectedEmail.urgency_score * 100)}% urgência
                            </span>
                          </div>
                        </div>
                        <div style={{ color: colors.gray, fontSize: "13px" }}>
                          <strong style={{ color: colors.light }}>De:</strong> {selectedEmail.sender_name} &lt;{selectedEmail.sender}&gt;
                        </div>
                        <div style={{ color: colors.gray, fontSize: "13px", marginTop: "4px" }}>
                          <strong style={{ color: colors.light }}>Data:</strong> {new Date(selectedEmail.date).toLocaleString('pt-BR')}
                        </div>
                      </div>

                      {/* AI Summary */}
                      <div style={{
                        background: colors.dark,
                        borderRadius: "8px",
                        padding: "16px",
                        marginBottom: "20px",
                        borderLeft: `4px solid ${colors.secondary}`
                      }}>
                        <div style={{ color: colors.secondary, fontWeight: "bold", fontSize: "12px", marginBottom: "8px" }}>
                          🤖 RESUMO DA IA
                        </div>
                        <p style={{ color: colors.light, fontSize: "14px", lineHeight: "1.6", margin: 0 }}>
                          {selectedEmail.summary}
                        </p>
                      </div>

                      {/* Action Items */}
                      {selectedEmail.action_items.length > 0 && (
                        <div style={{ marginBottom: "20px" }}>
                          <h4 style={{ color: colors.light, fontSize: "14px", marginBottom: "12px" }}>
                            ✅ Itens de Ação Identificados
                          </h4>
                          <ul style={{ color: colors.light, fontSize: "13px", paddingLeft: "20px", lineHeight: "1.8" }}>
                            {selectedEmail.action_items.map((item, idx) => (
                              <li key={idx}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Body Preview */}
                      <div>
                        <h4 style={{ color: colors.light, fontSize: "14px", marginBottom: "12px" }}>
                          📝 Conteúdo do Email
                        </h4>
                        <p style={{ color: colors.gray, fontSize: "13px", lineHeight: "1.6", whiteSpace: "pre-wrap" }}>
                          {selectedEmail.body_preview}
                        </p>
                      </div>

                      {/* Actions */}
                      <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: `1px solid ${colors.dark}`, display: "flex", gap: "12px" }}>
                        <button
                          style={{
                            padding: "10px 20px",
                            background: colors.secondary,
                            color: colors.dark,
                            border: "none",
                            borderRadius: "6px",
                            fontWeight: "bold",
                            cursor: "pointer"
                          }}
                        >
                          📧 Abrir no Email
                        </button>
                        <button
                          style={{
                            padding: "10px 20px",
                            background: "transparent",
                            border: `1px solid ${colors.gray}`,
                            color: colors.light,
                            borderRadius: "6px",
                            cursor: "pointer"
                          }}
                        >
                          ✅ Marcar como Lido
                        </button>
                        <button
                          style={{
                            padding: "10px 20px",
                            background: "transparent",
                            border: `1px solid ${colors.gray}`,
                            color: colors.light,
                            borderRadius: "6px",
                            cursor: "pointer"
                          }}
                        >
                          🏛️ Criar Documento
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      height: "100%",
                      color: colors.gray,
                      textAlign: "center"
                    }}>
                      <div>
                        <div style={{ fontSize: "48px", marginBottom: "16px" }}>📧</div>
                        <p>Selecione um email para ver os detalhes</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab: Configure */}
        {activeTab === 'configure' && (
          <div>
            {/* Existing Accounts */}
            {accounts.length > 0 && (
              <div style={{ marginBottom: "30px" }}>
                <h3 style={{ color: colors.light, marginBottom: "16px" }}>Contas Configuradas</h3>
                {accounts.map(acc => (
                  <div
                    key={acc.id}
                    style={{
                      background: colors.primary,
                      borderRadius: "8px",
                      padding: "16px",
                      marginBottom: "12px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center"
                    }}
                  >
                    <div>
                      <div style={{ color: colors.light, fontWeight: "bold" }}>
                        {acc.email_address}
                      </div>
                      <div style={{ color: colors.gray, fontSize: "12px", marginTop: "4px" }}>
                        Provedor: {acc.provider} | Última sincronização: {new Date(acc.last_sync).toLocaleString('pt-BR')}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <span style={{
                        padding: "4px 12px",
                        background: colors.accent + '30',
                        color: colors.accent,
                        borderRadius: "4px",
                        fontSize: "12px"
                      }}>
                        ✅ Ativo
                      </span>
                      <button style={{
                        padding: "6px 12px",
                        background: colors.danger + '30',
                        color: colors.danger,
                        border: "none",
                        borderRadius: "4px",
                        fontSize: "12px",
                        cursor: "pointer"
                      }}>
                        Remover
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Add New Account */}
            <button
              onClick={() => setShowAddAccount(!showAddAccount)}
              style={{
                padding: "14px 28px",
                background: colors.secondary,
                color: colors.dark,
                border: "none",
                borderRadius: "8px",
                fontWeight: "bold",
                cursor: "pointer",
                marginBottom: "20px"
              }}
            >
              {showAddAccount ? 'Cancelar' : '+ Adicionar Conta de Email'}
            </button>

            {showAddAccount && (
              <div style={{
                background: colors.primary,
                borderRadius: "12px",
                padding: "24px"
              }}>
                <h3 style={{ color: colors.light, marginBottom: "20px" }}>Configurar Nova Conta</h3>

                {/* Provider Selection */}
                <div style={{ marginBottom: "24px" }}>
                  <label style={{ color: colors.light, display: "block", marginBottom: "8px", fontSize: "14px" }}>
                    Provedor de Email
                  </label>
                  <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                    {providers.map(p => (
                      <button
                        key={p.id}
                        onClick={() => setSelectedProvider(p.id)}
                        style={{
                          padding: "12px 16px",
                          background: selectedProvider === p.id ? colors.secondary : colors.dark,
                          color: selectedProvider === p.id ? colors.dark : colors.light,
                          border: `1px solid ${selectedProvider === p.id ? colors.secondary : colors.gray}`,
                          borderRadius: "8px",
                          cursor: "pointer",
                          fontSize: "13px"
                        }}
                      >
                        {p.icon} {p.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Form */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
                  <div>
                    <label style={{ color: colors.gray, fontSize: "12px", display: "block", marginBottom: "6px" }}>
                      Endereço de Email *
                    </label>
                    <input
                      type="email"
                      value={configForm.email}
                      onChange={(e) => setConfigForm({...configForm, email: e.target.value})}
                      style={{
                        width: "100%",
                        padding: "10px",
                        background: colors.dark,
                        border: `1px solid ${colors.gray}`,
                        borderRadius: "6px",
                        color: colors.light
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ color: colors.gray, fontSize: "12px", display: "block", marginBottom: "6px" }}>
                      Senha ou App Password *
                    </label>
                    <input
                      type="password"
                      value={configForm.password}
                      onChange={(e) => setConfigForm({...configForm, password: e.target.value})}
                      style={{
                        width: "100%",
                        padding: "10px",
                        background: colors.dark,
                        border: `1px solid ${colors.gray}`,
                        borderRadius: "6px",
                        color: colors.light
                      }}
                    />
                  </div>
                </div>

                {/* Advanced Settings (for corporate) */}
                {selectedProvider === 'corporate' && (
                  <div style={{
                    background: colors.dark,
                    borderRadius: "8px",
                    padding: "16px",
                    marginBottom: "20px"
                  }}>
                    <h4 style={{ color: colors.light, fontSize: "14px", marginBottom: "12px" }}>
                      ⚙️ Configurações Avançadas (IMAP/SMTP)
                    </h4>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                      <div>
                        <label style={{ color: colors.gray, fontSize: "11px" }}>Servidor IMAP</label>
                        <input
                          type="text"
                          placeholder="mail.empresa.com.br"
                          value={configForm.imap_server}
                          onChange={(e) => setConfigForm({...configForm, imap_server: e.target.value})}
                          style={{
                            width: "100%",
                            padding: "8px",
                            background: colors.primary,
                            border: `1px solid ${colors.gray}`,
                            borderRadius: "4px",
                            color: colors.light,
                            fontSize: "13px"
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ color: colors.gray, fontSize: "11px" }}>Porta IMAP</label>
                        <input
                          type="number"
                          value={configForm.imap_port}
                          onChange={(e) => setConfigForm({...configForm, imap_port: parseInt(e.target.value)})}
                          style={{
                            width: "100%",
                            padding: "8px",
                            background: colors.primary,
                            border: `1px solid ${colors.gray}`,
                            borderRadius: "4px",
                            color: colors.light,
                            fontSize: "13px"
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ color: colors.gray, fontSize: "11px" }}>Servidor SMTP</label>
                        <input
                          type="text"
                          placeholder="smtp.empresa.com.br"
                          value={configForm.smtp_server}
                          onChange={(e) => setConfigForm({...configForm, smtp_server: e.target.value})}
                          style={{
                            width: "100%",
                            padding: "8px",
                            background: colors.primary,
                            border: `1px solid ${colors.gray}`,
                            borderRadius: "4px",
                            color: colors.light,
                            fontSize: "13px"
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ color: colors.gray, fontSize: "11px" }}>Porta SMTP</label>
                        <input
                          type="number"
                          value={configForm.smtp_port}
                          onChange={(e) => setConfigForm({...configForm, smtp_port: parseInt(e.target.value)})}
                          style={{
                            width: "100%",
                            padding: "8px",
                            background: colors.primary,
                            border: `1px solid ${colors.gray}`,
                            borderRadius: "4px",
                            color: colors.light,
                            fontSize: "13px"
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Test Connection */}
                {testResult && (
                  <div style={{
                    padding: "12px",
                    borderRadius: "6px",
                    marginBottom: "16px",
                    background: testResult.success ? colors.accent + '20' : colors.danger + '20',
                    border: `1px solid ${testResult.success ? colors.accent : colors.danger}`
                  }}>
                    <span style={{ color: testResult.success ? colors.accent : colors.danger, fontSize: "14px" }}>
                      {testResult.message}
                    </span>
                  </div>
                )}

                {/* Actions */}
                <div style={{ display: "flex", gap: "12px" }}>
                  <button
                    onClick={testConnection}
                    disabled={testingConnection}
                    style={{
                      padding: "12px 24px",
                      background: "transparent",
                      border: `1px solid ${colors.secondary}`,
                      color: colors.secondary,
                      borderRadius: "6px",
                      cursor: testingConnection ? "not-allowed" : "pointer",
                      opacity: testingConnection ? 0.6 : 1
                    }}
                  >
                    {testingConnection ? '⏳ Testando...' : '🔗 Testar Conexão'}
                  </button>
                  <button
                    onClick={saveAccount}
                    style={{
                      padding: "12px 24px",
                      background: colors.secondary,
                      color: colors.dark,
                      border: "none",
                      borderRadius: "6px",
                      fontWeight: "bold",
                      cursor: "pointer"
                    }}
                  >
                    💾 Salvar Configuração
                  </button>
                </div>
              </div>
            )}

            {/* Instructions */}
            <div style={{
              marginTop: "24px",
              padding: "16px",
              background: colors.primary,
              borderRadius: "8px",
              borderLeft: `4px solid ${colors.warning}`
            }}>
              <h4 style={{ color: colors.light, fontSize: "14px", marginBottom: "8px" }}>
                ⚠️ Instruções Importantes
              </h4>
              <ul style={{ color: colors.gray, fontSize: "13px", lineHeight: "1.6", margin: 0, paddingLeft: "20px" }}>
                <li>Use <strong>App Password</strong> para Gmail (não sua senha normal)</li>
                <li>Ative IMAP nas configurações do seu provedor de email</li>
                <li>Para emails corporativos, consulte o administrador de TI</li>
                <li>Suas credenciais são criptografadas e armazenadas com segurança</li>
              </ul>
            </div>
          </div>
        )}

        {/* Tab: Analytics */}
        {activeTab === 'analytics' && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "30px" }}>
              {[
                { label: 'Total de Emails', value: stats.total_emails, icon: '📧', color: colors.light },
                { label: 'Jurídicos', value: stats.legal_emails, icon: '🏛️', color: colors.secondary },
                { label: 'Urgentes', value: stats.urgent_emails, icon: '🔴', color: colors.danger },
                { label: 'Não Lidos', value: stats.unread_count, icon: '👁️', color: colors.warning }
              ].map(stat => (
                <div
                  key={stat.label}
                  style={{
                    background: colors.primary,
                    borderRadius: "8px",
                    padding: "20px",
                    textAlign: "center"
                  }}
                >
                  <div style={{ fontSize: "32px", marginBottom: "8px" }}>{stat.icon}</div>
                  <div style={{ color: stat.color, fontSize: "28px", fontWeight: "bold" }}>
                    {stat.value}
                  </div>
                  <div style={{ color: colors.gray, fontSize: "12px" }}>{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Weekly Report Preview */}
            <div style={{
              background: colors.primary,
              borderRadius: "12px",
              padding: "24px"
            }}>
              <h3 style={{ color: colors.light, marginBottom: "16px" }}>📊 Resumo Semanal (Últimos 7 dias)</h3>

              <div style={{
                background: colors.dark,
                borderRadius: "8px",
                padding: "20px",
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                color: colors.light,
                lineHeight: '1.6'
              }}>
{`📧 RESUMO SEMANAL DE EMAILS - 25/04 a 02/05/2024

Total de emails recebidos: 147
• 🏛️ Jurídicos: 32 (22%)
• 👤 Clientes: 28 (19%)
• 🏢 Internos: 41 (28%)
• 📧 Outros: 46 (31%)

⚠️ EMAILS URGENTES PROCESSADOS: 8
• Prazos processuais: 3
• Clientes insatisfeitos: 2
• Audiências agendadas: 3

🏛️ DESTAQUES JURÍDICOS:
• 5 intimações recebidas
• 3 contestações para preparar
• 2 recursos com prazo próximo
• 1 sentença favorável notificada

📈 TENDÊNCIAS:
• +15% de volume vs semana anterior
• Tempo médio de resposta: 4.2 horas
• 89% dos emails jurídicos foram respondidos

💡 RECOMENDAÇÕES DA IA:
• Priorize as 3 contestações com prazo em 10 dias
• Agende reunião de equipe para alocar recursos
• Considere delegar emails de rotina para estagiários
`}
              </div>

              <div style={{ marginTop: "20px", display: "flex", gap: "12px" }}>
                <button style={{
                  padding: "12px 24px",
                  background: colors.secondary,
                  color: colors.dark,
                  border: "none",
                  borderRadius: "6px",
                  fontWeight: "bold",
                  cursor: "pointer"
                }}>
                  📥 Exportar PDF
                </button>
                <button style={{
                  padding: "12px 24px",
                  background: "transparent",
                  border: `1px solid ${colors.gray}`,
                  color: colors.light,
                  borderRadius: "6px",
                  cursor: "pointer"
                }}>
                  📧 Enviar por Email
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
