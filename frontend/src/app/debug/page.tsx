"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { auth, db } from "@/lib/firebase";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  User
} from "firebase/auth";
import { doc, setDoc, getDoc, serverTimestamp } from "firebase/firestore";

export default function DebugPage() {
  const { devLogin } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [logs, setLogs] = useState<string[]>([]);
  const [testEmail, setTestEmail] = useState("test@example.com");
  const [testPassword, setTestPassword] = useState("password123");
  const [devEmail, setDevEmail] = useState("dev@neobusiness.ai");

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  useEffect(() => {
    addLog("Página de diagnóstico carregada");
    addLog(`URL atual: ${window.location.origin}`);
    addLog(`Host: ${window.location.host}`);

    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      addLog(currentUser ? `Usuário logado: ${currentUser.email}` : "Nenhum usuário logado");
    });

    return () => unsubscribe();
  }, []);

  const testEmailPasswordLogin = async () => {
    setLoading(true);
    setError("");
    addLog(`Tentando login com: ${testEmail}`);

    try {
      const result = await signInWithEmailAndPassword(auth, testEmail, testPassword);
      addLog(`✅ Login bem-sucedido: ${result.user.email}`);

      // Salvar no Firestore
      const userRef = doc(db, "users", result.user.uid);
      await setDoc(userRef, {
        uid: result.user.uid,
        email: result.user.email,
        lastLogin: serverTimestamp(),
      }, { merge: true });
      addLog("✅ Dados salvos no Firestore");

    } catch (err: any) {
      const errorMsg = err.message || err.code || "Erro desconhecido";
      setError(errorMsg);
      addLog(`❌ Erro no login: ${errorMsg}`);
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  const testCreateAccount = async () => {
    setLoading(true);
    setError("");
    const email = `test${Date.now()}@example.com`;
    addLog(`Criando conta: ${email}`);

    try {
      const result = await createUserWithEmailAndPassword(auth, email, "password123");
      addLog(`✅ Conta criada: ${result.user.email}`);

      await setDoc(doc(db, "users", result.user.uid), {
        uid: result.user.uid,
        email: result.user.email,
        createdAt: serverTimestamp(),
      });
      addLog("✅ Usuário salvo no Firestore");

    } catch (err: any) {
      const errorMsg = err.message || err.code || "Erro desconhecido";
      setError(errorMsg);
      addLog(`❌ Erro ao criar conta: ${errorMsg}`);
      console.error("Create error:", err);
    } finally {
      setLoading(false);
    }
  };

  const testGoogleLogin = async () => {
    setLoading(true);
    setError("");
    addLog("Tentando login com Google (Popup)...");

    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      addLog(`✅ Login Google bem-sucedido: ${result.user.email}`);
    } catch (err: any) {
      const errorMsg = err.message || err.code || "Erro desconhecido";
      setError(errorMsg);
      addLog(`❌ Erro no login Google (Popup): ${errorMsg}`);
      console.error("Google login error:", err);

      if (err.code === "auth/popup-blocked" || err.code === "auth/popup-closed-by-user") {
        addLog("💡 Tente usar o 'Login Google (Redirect)' abaixo");
      }
    } finally {
      setLoading(false);
    }
  };

  const testGoogleRedirect = async () => {
    setLoading(true);
    setError("");
    addLog("Redirecionando para login Google...");
    addLog("⚠️ A página vai recarregar após o login");

    try {
      const provider = new GoogleAuthProvider();
      await signInWithRedirect(auth, provider);
    } catch (err: any) {
      const errorMsg = err.message || err.code || "Erro desconhecido";
      setError(errorMsg);
      addLog(`❌ Erro no redirect: ${errorMsg}`);
      setLoading(false);
    }
  };

  // Verificar resultado do redirect ao carregar
  useEffect(() => {
    const checkRedirect = async () => {
      try {
        const result = await getRedirectResult(auth);
        if (result) {
          addLog(`✅ Login via redirect bem-sucedido: ${result.user.email}`);
        }
      } catch (err: any) {
        addLog(`❌ Erro no redirect result: ${err.message}`);
      }
    };
    checkRedirect();
  }, []);

  const handleDevLogin = () => {
    addLog(`🔧 Ativando modo desenvolvimento para: ${devEmail}`);
    devLogin(devEmail);
    addLog("✅ Modo desenvolvimento ativado! Redirecionando...");
    setTimeout(() => {
      window.location.href = "/chat";
    }, 1000);
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      addLog("✅ Logout realizado");
    } catch (err: any) {
      addLog(`❌ Erro no logout: ${err.message}`);
    }
  };

  return (
    <main style={{
      padding: "40px",
      maxWidth: "800px",
      margin: "0 auto",
      fontFamily: "system-ui",
      backgroundColor: "#ffffff",
      color: "#1a1a2e",
      minHeight: "100vh"
    }}>
      <h1 style={{ color: "#1a1a2e" }}>🔧 Diagnóstico Firebase</h1>

      <div style={{
        background: "#f0f0f0",
        padding: "20px",
        borderRadius: "8px",
        marginBottom: "20px",
        color: "#1a1a2e"
      }}>
        <h3 style={{ color: "#1a1a2e" }}>Status da Autenticação</h3>
        <p><strong>Usuário atual:</strong> {user ? `✅ ${user.email}` : "❌ Nenhum"}</p>
        <p><strong>UID:</strong> {user?.uid || "-"}</p>
      </div>

      {error && (
        <div style={{
          background: "#fee",
          color: "#c00",
          padding: "15px",
          borderRadius: "8px",
          marginBottom: "20px"
        }}>
          <strong>❌ Erro:</strong> {error}
        </div>
      )}

      {/* MODO DESENVOLVIMENTO */}
      <div style={{
        background: "#f3e5f5",
        padding: "20px",
        borderRadius: "8px",
        marginBottom: "20px",
        border: "3px solid #9c27b0"
      }}>
        <h3 style={{ color: "#6a1b9a" }}>🔧 MODO DESENVOLVIMENTO (Bypass)</h3>
        <p style={{ marginBottom: "15px", color: "#6a1b9a" }}>
          <strong>Funciona 100%!</strong> Entre sem precisar do Firebase/Google:
        </p>
        <div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
          <input
            type="email"
            value={devEmail}
            onChange={(e) => setDevEmail(e.target.value)}
            placeholder="Email para teste"
            style={{ padding: "12px", flex: 1, fontSize: "14px" }}
          />
        </div>
        <button
          onClick={handleDevLogin}
          disabled={loading}
          style={{
            padding: "15px 30px",
            cursor: "pointer",
            background: "#9c27b0",
            color: "white",
            fontSize: "16px",
            fontWeight: "bold",
            border: "none",
            borderRadius: "8px",
            width: "100%"
          }}
        >
          {loading ? "Entrando..." : "🚀 Entrar (Modo Desenvolvimento)"}
        </button>
        <p style={{ marginTop: "10px", fontSize: "12px", color: "#7b1fa2" }}>
          ⚠️ Apenas para testes locais. Não use em produção!
        </p>
      </div>

      <div style={{
        background: "#e8f5e9",
        padding: "20px",
        borderRadius: "8px",
        marginBottom: "20px",
        border: "2px solid #4caf50"
      }}>
        <h3 style={{ color: "#1a1a2e" }}>🚀 Login Rápido (Recomendado)</h3>
        <p style={{ marginBottom: "15px", color: "#1a1a2e" }}>
          Clique abaixo para entrar com sua conta Google principal:
        </p>
        <button
          onClick={testGoogleRedirect}
          disabled={loading}
          style={{
            padding: "15px 30px",
            cursor: "pointer",
            background: "#4285f4",
            color: "white",
            fontSize: "16px",
            fontWeight: "bold",
            border: "none",
            borderRadius: "8px",
            width: "100%"
          }}
        >
          {loading ? "Conectando..." : "🔵 Entrar com Google (campostrader1988@gmail.com)"}
        </button>
        <p style={{ marginTop: "10px", fontSize: "12px", color: "#666" }}>
          Isso vai redirecionar para o Google e voltar automaticamente
        </p>
      </div>

      <div style={{ marginBottom: "30px", color: "#1a1a2e" }}>
        <h3 style={{ color: "#1a1a2e" }}>Teste com Email/Senha</h3>
        <div style={{ display: "flex", gap: "10px", marginBottom: "10px", flexWrap: "wrap" }}>
          <input
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            placeholder="Email"
            style={{ padding: "10px", flex: 1, minWidth: "200px" }}
          />
          <input
            type="password"
            value={testPassword}
            onChange={(e) => setTestPassword(e.target.value)}
            placeholder="Senha"
            style={{ padding: "10px", flex: 1, minWidth: "200px" }}
          />
        </div>
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            onClick={testEmailPasswordLogin}
            disabled={loading}
            style={{ padding: "12px 20px", cursor: "pointer" }}
          >
            {loading ? "Testando..." : "Testar Login"}
          </button>
          <button
            onClick={testCreateAccount}
            disabled={loading}
            style={{ padding: "12px 20px", cursor: "pointer" }}
          >
            Criar Conta Teste
          </button>
          <button
            onClick={testGoogleLogin}
            disabled={loading}
            style={{ padding: "12px 20px", cursor: "pointer", background: "#4285f4", color: "white" }}
          >
            Google (Popup)
          </button>
          <button
            onClick={testGoogleRedirect}
            disabled={loading}
            style={{ padding: "12px 20px", cursor: "pointer", background: "#34a853", color: "white" }}
            title="Funciona melhor em localhost"
          >
            Google (Redirect) 🔄
          </button>
          {user && (
            <button
              onClick={handleLogout}
              style={{ padding: "12px 20px", cursor: "pointer", background: "#dc3545", color: "white" }}
            >
              Logout
            </button>
          )}
        </div>
      </div>

      <div>
        <h3>Logs</h3>
        <pre style={{
          background: "#1a1a2e",
          color: "#0f0",
          padding: "15px",
          borderRadius: "8px",
          maxHeight: "300px",
          overflow: "auto",
          fontSize: "12px",
          lineHeight: 1.5
        }}>
          {logs.length === 0 ? "Aguardando ações..." : logs.join("\n")}
        </pre>
      </div>

      <div style={{ marginTop: "30px", padding: "15px", background: "#ff4444", color: "white", borderRadius: "8px" }}>
        <h4>🚨 PROBLEMA IDENTIFICADO!</h4>
        <p style={{ lineHeight: 1.8, marginTop: "10px" }}>
          <strong>Seus usuários foram criados com Google OAuth (não têm senha!)</strong>
        </p>
        <ul style={{ lineHeight: 1.8 }}>
          <li><strong>campostrader1988@gmail.com</strong> → Criado via Google (SEM SENHA)</li>
          <li><strong>camposciro03@gmail.com</strong> → Criado via Google (SEM SENHA)</li>
          <li><strong>camposciro3@gmail.com</strong> → Criado via Google (SEM SENHA)</li>
          <li><strong>camposciro3@outlook.com</strong> → Criado via Google (SEM SENHA)</li>
        </ul>
        <p style={{ marginTop: "15px", fontSize: "16px" }}>
          <strong>✅ SOLUÇÃO:</strong> Use <strong>"Google (Redirect)"</strong> ou <strong>"Google (Popup)"</strong> para entrar!
          <br/>
          <strong>❌ NÃO ADIANTA:</strong> Tentar email/senha - essas contas não têm senha definida.
        </p>
      </div>

      <div style={{ marginTop: "30px", padding: "15px", background: "#fff3cd", borderRadius: "8px", color: "#856404" }}>
        <h4 style={{ color: "#856404" }}>📋 Resumo:</h4>
        <ol style={{ lineHeight: 1.8 }}>
          <li><strong>Para contas Google (campostrader1988@gmail.com, etc):</strong> Use botão verde "Google (Redirect)"</li>
          <li><strong>Para criar conta nova com senha:</strong> Use "Criar Conta Teste" com email novo</li>
          <li><strong>Domínios Autorizados:</strong> Adicione no Firebase Console:
            <ul style={{ marginTop: "5px" }}>
              <li><code>localhost</code></li>
              <li><code>localhost:3000</code></li>
              <li><code>127.0.0.1</code></li>
            </ul>
          </li>
        </ol>
        <p>
          <strong>Link Firebase:</strong>{" "}
          <a href="https://console.firebase.google.com/project/neobusinessai-37297/authentication/settings" target="_blank" rel="noopener noreferrer" style={{ color: "#856404" }}>
            Abrir Firebase Console
          </a>
        </p>
      </div>
    </main>
  );
}
