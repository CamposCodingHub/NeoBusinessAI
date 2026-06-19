"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";

export default function SettingsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [saving, setSaving] = useState(false);

  const [settings, setSettings] = useState({
    name: user?.displayName || "",
    email: user?.email || "",
    theme: "dark",
    language: "pt-BR",
    notifications: true,
    emailNotifications: true,
    soundEffects: true,
    autoSave: true,
  });

  const handleSave = async () => {
    setSaving(true);
    // Simula salvamento
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
    alert("Configurações salvas com sucesso!");
  };

  const tabs = [
    { id: "profile", label: "Perfil", icon: "👤" },
    { id: "appearance", label: "Aparência", icon: "🎨" },
    { id: "notifications", label: "Notificações", icon: "🔔" },
    { id: "privacy", label: "Privacidade", icon: "🔒" },
  ];

  return (
    <ProtectedRoute>
      <main className="settings-layout">
        <Sidebar />

        <div className="settings-main">
          {/* Header */}
          <header className="settings-header">
            <h1>⚙️ Configurações</h1>
            <p>Gerencie suas preferências e dados da conta</p>
          </header>

          <div className="settings-container">
            {/* Sidebar Tabs */}
            <div className="settings-tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`tab ${activeTab === tab.id ? "active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="settings-content">
              {activeTab === "profile" && (
                <div className="settings-section">
                  <h2>Informações do Perfil</h2>
                  <div className="avatar-section">
                    <div className="avatar">{user?.displayName?.[0] || "👤"}</div>
                    <button className="btn-secondary">Alterar foto</button>
                  </div>

                  <div className="form-group">
                    <label>Nome completo</label>
                    <input
                      type="text"
                      value={settings.name}
                      onChange={(e) =>
                        setSettings({ ...settings, name: e.target.value })
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label>Email</label>
                    <input
                      type="email"
                      value={settings.email}
                      disabled
                      className="disabled"
                    />
                    <span className="hint">Email não pode ser alterado</span>
                  </div>

                  <div className="form-group">
                    <label>Bio</label>
                    <textarea
                      rows={3}
                      placeholder="Conte um pouco sobre você..."
                    />
                  </div>
                </div>
              )}

              {activeTab === "appearance" && (
                <div className="settings-section">
                  <h2>Aparência</h2>

                  <div className="form-group">
                    <label>Tema</label>
                    <div className="theme-options">
                      <button
                        className={`theme-btn ${settings.theme === "dark" ? "active" : ""}`}
                        onClick={() => setSettings({ ...settings, theme: "dark" })}
                      >
                        <div className="theme-preview dark" />
                        <span>Escuro</span>
                      </button>
                      <button
                        className={`theme-btn ${settings.theme === "light" ? "active" : ""}`}
                        onClick={() => setSettings({ ...settings, theme: "light" })}
                      >
                        <div className="theme-preview light" />
                        <span>Claro</span>
                      </button>
                      <button
                        className={`theme-btn ${settings.theme === "system" ? "active" : ""}`}
                        onClick={() => setSettings({ ...settings, theme: "system" })}
                      >
                        <div className="theme-preview system" />
                        <span>Sistema</span>
                      </button>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Idioma</label>
                    <select
                      value={settings.language}
                      onChange={(e) =>
                        setSettings({ ...settings, language: e.target.value })
                      }
                    >
                      <option value="pt-BR">🇧🇷 Português (Brasil)</option>
                      <option value="en">🇺🇸 English</option>
                      <option value="es">🇪🇸 Español</option>
                    </select>
                  </div>

                  <div className="form-group toggle">
                    <label>Efeitos sonoros</label>
                    <button
                      className={`toggle-btn ${settings.soundEffects ? "active" : ""}`}
                      onClick={() =>
                        setSettings({ ...settings, soundEffects: !settings.soundEffects })
                      }
                    >
                      <span className="toggle-slider" />
                    </button>
                  </div>
                </div>
              )}

              {activeTab === "notifications" && (
                <div className="settings-section">
                  <h2>Notificações</h2>

                  <div className="form-group toggle">
                    <div>
                      <label>Notificações no app</label>
                      <span className="hint">Receba notificações sobre novas mensagens</span>
                    </div>
                    <button
                      className={`toggle-btn ${settings.notifications ? "active" : ""}`}
                      onClick={() =>
                        setSettings({ ...settings, notifications: !settings.notifications })
                      }
                    >
                      <span className="toggle-slider" />
                    </button>
                  </div>

                  <div className="form-group toggle">
                    <div>
                      <label>Notificações por email</label>
                      <span className="hint">Receba atualizações importantes no email</span>
                    </div>
                    <button
                      className={`toggle-btn ${settings.emailNotifications ? "active" : ""}`}
                      onClick={() =>
                        setSettings({ ...settings, emailNotifications: !settings.emailNotifications })
                      }
                    >
                      <span className="toggle-slider" />
                    </button>
                  </div>
                </div>
              )}

              {activeTab === "privacy" && (
                <div className="settings-section">
                  <h2>Privacidade e Segurança</h2>

                  <div className="form-group toggle">
                    <div>
                      <label>Salvar histórico automaticamente</label>
                      <span className="hint">Mantenha suas conversas salvas na nuvem</span>
                    </div>
                    <button
                      className={`toggle-btn ${settings.autoSave ? "active" : ""}`}
                      onClick={() => setSettings({ ...settings, autoSave: !settings.autoSave })}
                    >
                      <span className="toggle-slider" />
                    </button>
                  </div>

                  <div className="danger-zone">
                    <h3>🚨 Zona de Perigo</h3>
                    <p>Ações irreversíveis para sua conta</p>
                    <button className="btn-danger">Excluir minha conta</button>
                  </div>
                </div>
              )}

              <div className="settings-actions">
                <button className="btn-secondary" onClick={() => router.push("/chat")}>
                  Cancelar
                </button>
                <button
                  className="btn-primary"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? "Salvando..." : "Salvar alterações"}
                </button>
              </div>
            </div>
          </div>
        </div>

        <style jsx>{`
          .settings-layout {
            display: flex;
            min-height: 100vh;
            background: #020617;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          }

          .settings-main {
            flex: 1;
            margin-left: 280px;
            padding: 32px;
          }

          .settings-header {
            margin-bottom: 32px;
          }

          .settings-header h1 {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
          }

          .settings-header p {
            color: rgba(255, 255, 255, 0.5);
            font-size: 15px;
          }

          .settings-container {
            display: flex;
            gap: 32px;
            max-width: 1000px;
          }

          .settings-tabs {
            width: 240px;
            flex-shrink: 0;
          }

          .tab {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            background: transparent;
            border: none;
            border-radius: 12px;
            color: rgba(255, 255, 255, 0.6);
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 4px;
          }

          .tab:hover {
            background: rgba(255, 255, 255, 0.05);
            color: white;
          }

          .tab.active {
            background: rgba(99, 102, 241, 0.15);
            color: #6366f1;
          }

          .settings-content {
            flex: 1;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 32px;
          }

          .settings-section h2 {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 24px;
          }

          .avatar-section {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
          }

          .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            font-weight: 600;
          }

          .form-group {
            margin-bottom: 24px;
          }

          .form-group.toggle {
            display: flex;
            align-items: center;
            justify-content: space-between;
          }

          .form-group label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
            color: rgba(255, 255, 255, 0.9);
          }

          .form-group input,
          .form-group textarea,
          .form-group select {
            width: 100%;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: white;
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
          }

          .form-group input:focus,
          .form-group textarea:focus,
          .form-group select:focus {
            border-color: #6366f1;
            background: rgba(255, 255, 255, 0.08);
          }

          .form-group input.disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .hint {
            display: block;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.4);
            margin-top: 6px;
          }

          .theme-options {
            display: flex;
            gap: 16px;
          }

          .theme-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 2px solid transparent;
            border-radius: 12px;
            color: white;
            cursor: pointer;
            transition: all 0.2s;
          }

          .theme-btn:hover {
            background: rgba(255, 255, 255, 0.08);
          }

          .theme-btn.active {
            border-color: #6366f1;
            background: rgba(99, 102, 241, 0.1);
          }

          .theme-preview {
            width: 60px;
            height: 40px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.2);
          }

          .theme-preview.dark {
            background: #1a1a2e;
          }

          .theme-preview.light {
            background: #f1f5f9;
          }

          .theme-preview.system {
            background: linear-gradient(135deg, #1a1a2e 50%, #f1f5f9 50%);
          }

          .toggle-btn {
            width: 48px;
            height: 26px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 13px;
            position: relative;
            cursor: pointer;
            transition: all 0.2s;
          }

          .toggle-btn.active {
            background: #6366f1;
          }

          .toggle-slider {
            position: absolute;
            top: 3px;
            left: 3px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: all 0.2s;
          }

          .toggle-btn.active .toggle-slider {
            transform: translateX(22px);
          }

          .danger-zone {
            margin-top: 40px;
            padding: 24px;
            background: rgba(239, 68, 68, 0.05);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 12px;
          }

          .danger-zone h3 {
            font-size: 16px;
            font-weight: 600;
            color: #ef4444;
            margin-bottom: 8px;
          }

          .danger-zone p {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.5);
            margin-bottom: 16px;
          }

          .settings-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
          }

          .btn-primary {
            padding: 12px 24px;
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
          }

          .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
          }

          .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }

          .btn-secondary {
            padding: 12px 24px;
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: white;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
          }

          .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.05);
          }

          .btn-danger {
            padding: 10px 20px;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            color: #ef4444;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
          }

          .btn-danger:hover {
            background: rgba(239, 68, 68, 0.2);
          }

          @media (max-width: 768px) {
            .settings-main {
              margin-left: 0;
              padding: 20px;
            }

            .settings-container {
              flex-direction: column;
            }

            .settings-tabs {
              width: 100%;
              display: flex;
              overflow-x: auto;
            }

            .tab {
              white-space: nowrap;
            }

            .theme-options {
              flex-wrap: wrap;
            }
          }
        `}</style>
      </main>
    </ProtectedRoute>
  );
}
