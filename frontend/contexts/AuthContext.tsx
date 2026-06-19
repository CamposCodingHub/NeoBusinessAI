'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';

// ==================== TYPES ====================

export interface User {
  id: number;
  email: string;
  name: string;
  role: 'user' | 'premium' | 'enterprise' | 'admin';
  plan_tier: 'free' | 'starter' | 'professional' | 'business' | 'enterprise';
  subscription_status: string;
  documents_limit: number;
  users_limit: number;
  last_login?: string;
  created_at?: string;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  checkAuth: () => Promise<boolean>;
  updateUser: (userData: Partial<User>) => void;
}

interface RegisterData {
  email: string;
  password: string;
  name: string;
  company?: string;
  phone?: string;
  use_case?: string;
}

// ==================== CONSTANTS ====================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'neobusiness_tokens';
const USER_KEY = 'neobusiness_user';

function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;

  try {
    const storedUser = localStorage.getItem(USER_KEY);
    return storedUser ? (JSON.parse(storedUser) as User) : null;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

// Rotas públicas (não precisam de autenticação)
const PUBLIC_ROUTES = ['/', '/login', '/register', '/pricing', '/forgot-password', '/reset-password'];

// Rotas que exigem plano específico
const PROTECTED_ROUTES = {
  '/dashboard': ['user', 'premium', 'enterprise', 'admin'],
  '/chat': ['user', 'premium', 'enterprise', 'admin'],
  '/documents': ['user', 'premium', 'enterprise', 'admin'],
  '/reports': ['premium', 'enterprise', 'admin'],
  '/team': ['enterprise', 'admin'],
  '/admin': ['admin'],
};

// ==================== CONTEXT ====================

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser());
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // ==================== INITIALIZATION ====================
  // Verificar auth apenas uma vez na montagem
  useEffect(() => {
    checkAuth();
  }, []);

  // ==================== AUTH FUNCTIONS ====================

  const checkAuth = async (): Promise<boolean> => {
    try {
      const tokens = getTokens();
      if (!tokens?.access_token) {
        console.log('[checkAuth] Nenhum token encontrado');
        setUser(null);
        setIsLoading(false);
        return false;
      }

      console.log('[checkAuth] Verificando token...');
      // Verificar se token ainda é válido buscando dados do usuário
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'omit',
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem(USER_KEY, JSON.stringify(userData));
        console.log('[checkAuth] Token válido, usuário:', userData.email);
        setIsLoading(false);
        return true;
      } else if (response.status === 401) {
        // Token expirado, tentar refresh
        console.log('[checkAuth] Token expirado, tentando refresh...');
        const refreshed = await refreshToken();
        setIsLoading(false);
        return refreshed;
      } else {
        // Outro erro (ex: 500) - NÃO limpar auth, pode ser erro temporário
        console.warn('[checkAuth] Erro', response.status, '- mantendo sessão');
        setIsLoading(false);
        return false;
      }
    } catch (error) {
      // Erro de rede - NÃO limpar auth
      console.warn('[checkAuth] Erro de rede, mantendo sessão:', error);
      setIsLoading(false);
      return false;
    }
  };

  const login = async (email: string, password: string): Promise<void> => {
    try {
      console.log('[AuthContext] Iniciando fetch para /auth/login...');
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'omit',
      });
      console.log('[AuthContext] Resposta recebida:', response.status);

      if (!response.ok) {
        const error = await response.json();
        console.error('[AuthContext] Erro na resposta:', error);
        throw new Error(error.detail || 'Login falhou');
      }

      const data = await response.json();
      console.log('[AuthContext] Dados recebidos:', { hasToken: !!data.access_token, user: data.user?.email });

      // Salvar tokens
      saveTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type,
      });
      console.log('[AuthContext] Tokens salvos');

      // Salvar usuário
      setUser(data.user);
      localStorage.setItem(USER_KEY, JSON.stringify(data.user));
      console.log('[AuthContext] Usuário salvo');

      // Redirecionar direto ao dashboard
      console.log('[AuthContext] Redirecionando para /dashboard');
      window.location.href = '/dashboard';
    } catch (error: any) {
      console.error('[AuthContext] Erro no login:', error);
      throw error;
    }
  };

  const register = async (userData: RegisterData): Promise<void> => {
    try {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
        credentials: 'omit',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registro falhou');
      }

      const data = await response.json();

      // Salvar tokens
      saveTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type,
      });

      // Criar objeto usuário do registro
      const newUser: User = {
        id: data.user_id,
        email: userData.email,
        name: userData.name,
        role: 'user',
        plan_tier: 'free',
        subscription_status: 'inactive',
        documents_limit: 5,
        users_limit: 1,
      };

      setUser(newUser);
      localStorage.setItem(USER_KEY, JSON.stringify(newUser));

      // Sempre redirecionar para onboarding após registro
      router.push('/onboarding');
    } catch (error) {
      console.error('Register error:', error);
      throw error;
    }
  };

  const logout = (): void => {
    clearAuth();
    router.push('/login');
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const tokens = getTokens();
      if (!tokens?.refresh_token) return false;

      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokens.refresh_token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'omit',
      });

      if (response.ok) {
        const data = await response.json();
        saveTokens({
          access_token: data.access_token,
          refresh_token: tokens.refresh_token,
          token_type: data.token_type,
        });
        return true;
      } else {
        clearAuth();
        return false;
      }
    } catch (error) {
      console.error('Refresh token error:', error);
      clearAuth();
      return false;
    }
  };

  const updateUser = (userData: Partial<User>): void => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
    }
  };

  // ==================== HELPERS ====================

  // DESATIVADO - estava causando loop infinito
  // Proteção de rotas manual em cada página
  const protectRoute = () => {
    // Não faz nada automático - cada página cuida da própria proteção
    return;
  };

  const getTokens = (): AuthTokens | null => {
    if (typeof window === 'undefined') return null;
    const tokens = localStorage.getItem(TOKEN_KEY);
    return tokens ? JSON.parse(tokens) : null;
  };

  const saveTokens = (tokens: AuthTokens): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  };

  const clearAuth = (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  };

  // ==================== API HELPER ====================

  // Função para fazer requisições autenticadas
  const authFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
    const tokens = getTokens();

    const authOptions = {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${tokens?.access_token}`,
        'Content-Type': 'application/json',
      },
    };

    let response = await fetch(url, authOptions);

    // Se token expirou, tenta refresh
    if (response.status === 401) {
      const refreshed = await refreshToken();
      if (refreshed) {
        const newTokens = getTokens();
        authOptions.headers = {
          ...authOptions.headers,
          'Authorization': `Bearer ${newTokens?.access_token}`,
        };
        response = await fetch(url, authOptions);
      } else {
        // Refresh falhou, redireciona para login
        logout();
      }
    }

    return response;
  };

  // ==================== RENDER ====================

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
    checkAuth,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// ==================== HOOK ====================

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// ==================== HOC ====================

export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  requiredRole?: string
): React.FC<P> {
  return function WithAuthComponent(props: P) {
    const { user, isLoading, isAuthenticated } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!isLoading) {
        if (!isAuthenticated) {
          router.push('/login');
        } else if (requiredRole && user?.role !== requiredRole) {
          router.push('/pricing');
        }
      }
    }, [isLoading, isAuthenticated, user]);

    if (isLoading) {
      return (
        <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500" />
        </div>
      );
    }

    if (!isAuthenticated) {
      return null;
    }

    if (requiredRole && user?.role !== requiredRole) {
      return null;
    }

    return <Component {...props} />;
  };
}

export default AuthContext;
