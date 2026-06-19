"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function RegisterPage() {
  const router = useRouter();
  const { register, login, loginWithGoogle } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (password !== confirmPassword) {
      setError("As senhas não coincidem");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("A senha deve ter pelo menos 8 caracteres");
      setLoading(false);
      return;
    }

    if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password) || !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      setError("Use pelo menos 1 maiúscula, 1 minúscula, 1 número e 1 caractere especial");
      setLoading(false);
      return;
    }

    try {
      await register(email, password, name);
      router.push("/onboarding");
    } catch (err: any) {
      // Se email já existe, tenta fazer login automaticamente
      if (err.message?.includes("já está em uso") || err.message?.includes("already in use")) {
        setError("Email já cadastrado! Tentando fazer login...");
        try {
          await login(email, password);
          const onboardingCompleted = typeof window !== "undefined" && localStorage.getItem("onboarding_completed") === "true";
          router.push(onboardingCompleted ? "/dashboard" : "/onboarding");
          return;
        } catch (loginErr: any) {
          setError("Conta já existe! Vá para a página de login ou use a senha correta.");
        }
      } else {
        setError(err.message || "Erro ao criar conta");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError("");

    try {
      await loginWithGoogle();
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Erro ao fazer login com Google");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      {/* Background Effects */}
      <div className="auth-bg">
        <div className="glow-orb orb-1" />
        <div className="glow-orb orb-2" />
      </div>

      <div className="auth-container">
        {/* Logo */}
        <div className="auth-brand">
          <span className="brand-icon">🧠</span>
          <h1>NeoBusiness AI</h1>
          <p>Sua IA especialista em negócios</p>
        </div>

        {/* Form Card */}
        <div className="auth-card">
          <h2>Criar conta</h2>
          <p className="auth-subtitle">Comece gratuitamente hoje</p>

          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="input-group">
              <label>Nome completo</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Seu nome"
                required
                disabled={loading}
              />
            </div>

            <div className="input-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                disabled={loading}
              />
            </div>

            <div className="input-group">
              <label>Senha</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mínimo 6 caracteres"
                required
                disabled={loading}
              />
            </div>

            <div className="input-group">
              <label>Confirmar senha</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className="btn-submit"
              disabled={loading || !name || !email || !password || !confirmPassword}
            >
              {loading ? "Criando conta..." : "Criar conta grátis"}
            </button>
          </form>

          <div className="auth-divider">
            <span>ou continue com</span>
          </div>

          <div className="social-login">
            <button
              className="btn-social google"
              onClick={handleGoogleLogin}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span>Google</span>
            </button>
          </div>

          <p className="auth-footer">
            Já tem uma conta?{" "}
            <a href="/login" onClick={(e) => { e.preventDefault(); router.push("/login"); }}>
              Entrar
            </a>
          </p>
        </div>
      </div>

      <style jsx>{`
        .auth-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #020617;
          position: relative;
          overflow: hidden;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
        }

        .auth-bg {
          position: fixed;
          inset: 0;
          z-index: 0;
        }

        .glow-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(100px);
          opacity: 0.4;
        }

        .orb-1 {
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, #6366f1, transparent);
          top: -200px;
          left: -100px;
        }

        .orb-2 {
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, #a855f7, transparent);
          bottom: -150px;
          right: -100px;
        }

        .auth-container {
          position: relative;
          z-index: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 32px;
          padding: 20px;
          width: 100%;
          max-width: 420px;
        }

        .auth-brand {
          text-align: center;
          color: white;
        }

        .brand-icon {
          font-size: 48px;
          display: block;
          margin-bottom: 16px;
        }

        .auth-brand h1 {
          font-size: 28px;
          font-weight: 700;
          margin-bottom: 8px;
          background: linear-gradient(135deg, #6366f1, #a855f7);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .auth-brand p {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.5);
        }

        .auth-card {
          width: 100%;
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 24px;
          padding: 40px;
        }

        .auth-card h2 {
          font-size: 24px;
          font-weight: 700;
          color: white;
          margin-bottom: 8px;
          text-align: center;
        }

        .auth-subtitle {
          font-size: 14px;
          color: rgba(255, 255, 255, 0.5);
          text-align: center;
          margin-bottom: 32px;
        }

        .auth-error {
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          color: #ef4444;
          padding: 12px;
          border-radius: 10px;
          font-size: 13px;
          margin-bottom: 20px;
          text-align: center;
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .input-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .input-group label {
          font-size: 13px;
          font-weight: 500;
          color: rgba(255, 255, 255, 0.7);
        }

        .input-group input {
          padding: 14px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          color: white;
          font-size: 15px;
          outline: none;
          transition: all 0.2s;
        }

        .input-group input:focus {
          border-color: #6366f1;
          background: rgba(255, 255, 255, 0.08);
        }

        .input-group input::placeholder {
          color: rgba(255, 255, 255, 0.3);
        }

        .input-group input:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-submit {
          padding: 14px;
          background: linear-gradient(135deg, #4f46e5, #6366f1);
          border: none;
          border-radius: 12px;
          color: white;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          margin-top: 8px;
        }

        .btn-submit:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
        }

        .btn-submit:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .auth-divider {
          display: flex;
          align-items: center;
          gap: 16px;
          margin: 28px 0;
          color: rgba(255, 255, 255, 0.4);
          font-size: 13px;
        }

        .auth-divider::before,
        .auth-divider::after {
          content: "";
          flex: 1;
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
        }

        .social-login {
          display: flex;
          gap: 12px;
        }

        .btn-social {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          color: white;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-social:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.2);
        }

        .btn-social:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .auth-footer {
          text-align: center;
          margin-top: 28px;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.5);
        }

        .auth-footer a {
          color: #6366f1;
          text-decoration: none;
          font-weight: 600;
          transition: color 0.2s;
        }

        .auth-footer a:hover {
          color: #818cf8;
        }

        @media (max-width: 480px) {
          .auth-card {
            padding: 28px;
          }

          .auth-brand h1 {
            font-size: 24px;
          }
        }
      `}</style>
    </main>
  );
}
