"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setError("Token inválido ou ausente. Solicite uma nova recuperação.");
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

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

    try {
      const response = await fetch("http://localhost:8000/auth/reset-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        setMessage(data.message);
        setTimeout(() => {
          router.push("/login");
        }, 3000);
      } else {
        setError(data.detail || "Erro ao redefinir senha");
      }
    } catch (err) {
      setError("Erro de conexão com o servidor");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white/5 rounded-2xl p-8 border border-white/10 text-center">
          <div className="text-5xl mb-4">✅</div>
          <h1 className="text-2xl font-bold text-white mb-4">
            Senha redefinida!
          </h1>
          <p className="text-green-400 mb-6">{message}</p>
          <p className="text-white/60 mb-6">
            Redirecionando para login em 3 segundos...
          </p>
          <Link
            href="/login"
            className="text-blue-400 hover:text-blue-300"
          >
            Ir para login agora →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white/5 rounded-2xl p-8 border border-white/10">
        <h1 className="text-3xl font-bold text-white mb-2 text-center">
          Nova Senha
        </h1>
        <p className="text-white/60 text-center mb-8">
          Defina sua nova senha de acesso
        </p>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400 text-center">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-2">Nova Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
              placeholder="Mínimo 8 caracteres"
            />
          </div>

          <div>
            <label className="block text-sm text-white/60 mb-2">Confirmar Senha</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
              placeholder="Repita a senha"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !token}
            className="w-full py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-lg font-semibold hover:opacity-90 transition disabled:opacity-50"
          >
            {loading ? "Redefinindo..." : "Redefinir senha"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link href="/login" className="text-blue-400 hover:text-blue-300 text-sm">
            ← Voltar para login
          </Link>
        </div>
      </div>
    </div>
  );
}
