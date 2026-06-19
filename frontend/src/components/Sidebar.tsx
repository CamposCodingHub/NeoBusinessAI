"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { auth } from "@/lib/firebase";
import { signOut } from "firebase/auth";

interface Chat {
  id: string;
  title: string;
  timestamp: number;
}

interface SidebarProps {
  chatHistory?: Chat[];
  onSelectChat?: (chatId: string) => void;
  onNewChat?: () => void;
  currentChatId?: string;
}

export default function Sidebar({
  chatHistory = [],
  onSelectChat,
  onNewChat,
  currentChatId,
}: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      router.push("/login");
    } catch (error) {
      console.error("Erro ao sair:", error);
    }
  };

  const navItems = [
    { path: "/", icon: "🏠", label: "Início" },
    { path: "/dashboard", icon: "⚖️", label: "Dashboard" },
    { path: "/chat", icon: "💬", label: "Chat" },
    { path: "/email-integration", icon: "📧", label: "Email IA", badge: "PRO" },
    { path: "/pricing", icon: "💰", label: "Planos" },
    { path: "/settings", icon: "⚙️", label: "Configurações" },
    { path: "/help", icon: "❓", label: "Ajuda" },
  ];

  return (
    <>
      <aside className={`sidebar ${isCollapsed ? "collapsed" : ""}`} style={{ background: "#1e3a5f" }}>
        {/* Logo */}
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">⚖️</span>
            {!isCollapsed && <span className="logo-text">LexScan IA</span>}
          </div>
          <button
            className="collapse-btn"
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? "Expandir" : "Recolher"}
          >
            {isCollapsed ? "→" : "←"}
          </button>
        </div>

        {/* Novo Chat */}
        <button className="new-chat-btn" onClick={onNewChat}>
          <span>+</span>
          {!isCollapsed && <span>Novo Chat</span>}
        </button>

        {/* Navegação Principal */}
        <nav className="main-nav">
          {navItems.map((item) => (
            <button
              key={item.path}
              className={`nav-item ${pathname === item.path ? "active" : ""}`}
              onClick={() => router.push(item.path)}
            >
              <span className="nav-icon">{item.icon}</span>
              {!isCollapsed && <span className="nav-label">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Histórico de Chats */}
        {!isCollapsed && chatHistory.length > 0 && (
          <div className="chat-history">
            <h3>Histórico</h3>
            <div className="history-list">
              {chatHistory.map((chat) => (
                <button
                  key={chat.id}
                  className={`history-item ${
                    currentChatId === chat.id ? "active" : ""
                  }`}
                  onClick={() => onSelectChat?.(chat.id)}
                >
                  <span className="history-icon">💬</span>
                  <span className="history-title">{chat.title}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="sidebar-footer">
          {!isCollapsed && (
            <div className="user-info">
              <div className="user-avatar">👤</div>
              <span className="user-name">Usuário</span>
            </div>
          )}
          <button
            className="logout-btn"
            onClick={handleLogout}
            title="Sair"
          >
            <span>🚪</span>
            {!isCollapsed && <span>Sair</span>}
          </button>
        </div>
      </aside>

      <style jsx>{`
        .sidebar {
          width: 280px;
          height: 100vh;
          background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
          border-right: 1px solid rgba(255, 255, 255, 0.1);
          display: flex;
          flex-direction: column;
          transition: width 0.3s ease;
          position: fixed;
          left: 0;
          top: 0;
          z-index: 100;
        }

        .sidebar.collapsed {
          width: 70px;
        }

        .sidebar-header {
          padding: 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .logo-icon {
          font-size: 24px;
        }

        .logo-text {
          font-weight: 700;
          font-size: 18px;
          background: linear-gradient(135deg, #6366f1, #a855f7);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .collapse-btn {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: white;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        }

        .collapse-btn:hover {
          background: rgba(255, 255, 255, 0.2);
        }

        .new-chat-btn {
          margin: 16px;
          padding: 12px 16px;
          background: linear-gradient(135deg, #4f46e5, #6366f1);
          border: none;
          border-radius: 12px;
          color: white;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: all 0.2s;
        }

        .new-chat-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
        }

        .sidebar.collapsed .new-chat-btn {
          padding: 12px;
        }

        .main-nav {
          padding: 0 12px;
        }

        .nav-item {
          width: 100%;
          padding: 12px 16px;
          margin-bottom: 4px;
          background: transparent;
          border: none;
          border-radius: 10px;
          color: rgba(255, 255, 255, 0.7);
          display: flex;
          align-items: center;
          gap: 12px;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 14px;
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.05);
          color: white;
        }

        .nav-item.active {
          background: rgba(99, 102, 241, 0.2);
          color: #6366f1;
        }

        .nav-icon {
          font-size: 18px;
          width: 24px;
          text-align: center;
        }

        .chat-history {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          margin-top: 8px;
        }

        .chat-history h3 {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: rgba(255, 255, 255, 0.4);
          margin-bottom: 12px;
          padding-left: 12px;
        }

        .history-list {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .history-item {
          width: 100%;
          padding: 10px 12px;
          background: transparent;
          border: none;
          border-radius: 8px;
          color: rgba(255, 255, 255, 0.7);
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 13px;
          text-align: left;
        }

        .history-item:hover {
          background: rgba(255, 255, 255, 0.05);
          color: white;
        }

        .history-item.active {
          background: rgba(99, 102, 241, 0.15);
          color: #6366f1;
        }

        .history-icon {
          font-size: 14px;
        }

        .history-title {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          flex: 1;
        }

        .sidebar-footer {
          padding: 16px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 12px;
          padding: 8px;
          border-radius: 10px;
          background: rgba(255, 255, 255, 0.03);
        }

        .user-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #4f46e5, #6366f1);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
        }

        .user-name {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.9);
        }

        .logout-btn {
          width: 100%;
          padding: 10px 16px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: 10px;
          color: #ef4444;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 14px;
        }

        .logout-btn:hover {
          background: rgba(239, 68, 68, 0.2);
        }

        .sidebar.collapsed .logout-btn {
          padding: 10px;
        }

        @media (max-width: 768px) {
          .sidebar {
            transform: translateX(-100%);
          }

          .sidebar.open {
            transform: translateX(0);
          }
        }
      `}</style>
    </>
  );
}
