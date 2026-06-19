"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";

export interface AuthUser {
  id: number | string;
  uid?: string;
  email: string;
  name: string;
  displayName: string;
  role: "user" | "premium" | "enterprise" | "admin";
  plan_tier: "free" | "starter" | "professional" | "business" | "enterprise";
  subscription_status: string;
  documents_limit: number;
  users_limit: number;
  created_at?: string;
  last_login?: string;
  photoURL?: string | null;
  emailVerified?: boolean;
  isAnonymous?: boolean;
  phoneNumber?: string | null;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface RegisterOptions {
  company?: string;
  phone?: string;
  use_case?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    name: string,
    options?: RegisterOptions
  ) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  devLogin: (email: string) => void;
  refreshToken: () => Promise<boolean>;
  checkAuth: () => Promise<boolean>;
  updateUser: (userData: Partial<AuthUser>) => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const TOKEN_KEY = "neobusiness_tokens";
const USER_KEY = "neobusiness_user";
const DEV_USER_KEY = "devUser";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function normalizeUser(raw: any): AuthUser {
  const email = raw?.email || "";
  const displayName =
    raw?.displayName || raw?.name || (email ? email.split("@")[0] : "Usuario");

  return {
    id: raw?.id ?? raw?.uid ?? Date.now(),
    uid: String(raw?.uid ?? raw?.id ?? Date.now()),
    email,
    name: raw?.name || displayName,
    displayName,
    role: raw?.role || "user",
    plan_tier: raw?.plan_tier || "free",
    subscription_status: raw?.subscription_status || "inactive",
    documents_limit: raw?.documents_limit ?? 5,
    users_limit: raw?.users_limit ?? 1,
    created_at: raw?.created_at,
    last_login: raw?.last_login,
    photoURL: raw?.photoURL ?? null,
    emailVerified: raw?.emailVerified ?? true,
    isAnonymous: raw?.isAnonymous ?? false,
    phoneNumber: raw?.phoneNumber ?? null,
  };
}

async function extractError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((item: any) => item.msg || item.message || "Erro de validacao").join(" | ");
    }
    if (typeof data?.message === "string") return data.message;
  } catch {
    // ignore
  }
  return `Erro HTTP ${response.status}`;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const getTokens = (): AuthTokens | null => {
    if (typeof window === "undefined") return null;
    const tokens = localStorage.getItem(TOKEN_KEY);
    return tokens ? JSON.parse(tokens) : null;
  };

  const saveTokens = (tokens: AuthTokens): void => {
    if (typeof window === "undefined") return;
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  };

  const saveUser = (nextUser: AuthUser | null): void => {
    setUser(nextUser);
    if (typeof window === "undefined") return;
    if (nextUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  };

  const clearAuth = (): void => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
    setUser(null);
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const tokens = getTokens();
      if (!tokens?.refresh_token) return false;

      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${tokens.refresh_token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        clearAuth();
        return false;
      }

      const data = await response.json();
      saveTokens({
        access_token: data.access_token,
        refresh_token: tokens.refresh_token,
        token_type: data.token_type || tokens.token_type || "bearer",
      });
      return true;
    } catch (error) {
      console.error("[Auth] Erro no refresh:", error);
      clearAuth();
      return false;
    }
  };

  const checkAuth = async (): Promise<boolean> => {
    try {
      if (typeof window !== "undefined") {
        const devUser = localStorage.getItem(DEV_USER_KEY);
        if (devUser && !getTokens()) {
          saveUser(normalizeUser(JSON.parse(devUser)));
          setLoading(false);
          return true;
        }
      }

      const tokens = getTokens();
      if (!tokens?.access_token) {
        setLoading(false);
        return false;
      }

      let response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${tokens.access_token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        const refreshed = await refreshToken();
        if (!refreshed) {
          setLoading(false);
          return false;
        }
        const nextTokens = getTokens();
        response = await fetch(`${API_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${nextTokens?.access_token}`,
            "Content-Type": "application/json",
          },
        });
      }

      if (!response.ok) {
        clearAuth();
        setLoading(false);
        return false;
      }

      const data = await response.json();
      saveUser(normalizeUser(data));
      setLoading(false);
      return true;
    } catch (error) {
      console.warn("[Auth] checkAuth falhou:", error);
      setLoading(false);
      return false;
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error(await extractError(response));
    }

    const data = await response.json();
    saveTokens({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      token_type: data.token_type || "bearer",
    });
    saveUser(normalizeUser(data.user));
  };

  const register = async (
    email: string,
    password: string,
    name: string,
    options?: RegisterOptions
  ) => {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        name,
        ...options,
      }),
    });

    if (!response.ok) {
      throw new Error(await extractError(response));
    }

    const data = await response.json();
    saveTokens({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      token_type: data.token_type || "bearer",
    });
    saveUser(
      normalizeUser({
        id: data.user_id,
        email,
        name,
        role: "user",
        plan_tier: "free",
        subscription_status: "inactive",
        documents_limit: 5,
        users_limit: 1,
      })
    );
  };

  const loginWithGoogle = async () => {
    throw new Error(
      "Login com Google ainda nao esta integrado ao backend. Use email e senha por enquanto."
    );
  };

  const logout = async () => {
    try {
      const tokens = getTokens();
      if (tokens?.access_token) {
        await fetch(`${API_URL}/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${tokens.access_token}`,
            "Content-Type": "application/json",
          },
        });
      }
    } catch (error) {
      console.warn("[Auth] Logout remoto falhou:", error);
    } finally {
      if (typeof window !== "undefined") {
        localStorage.removeItem(DEV_USER_KEY);
      }
      clearAuth();
    }
  };

  const devLogin = (email: string) => {
    const mockUser = normalizeUser({
      id: `dev-${Date.now()}`,
      uid: `dev-${Date.now()}`,
      email,
      name: email.split("@")[0],
      displayName: email.split("@")[0],
      role: "admin",
      plan_tier: "enterprise",
      subscription_status: "active",
      documents_limit: 999,
      users_limit: 999,
    });

    if (typeof window !== "undefined") {
      localStorage.setItem(DEV_USER_KEY, JSON.stringify(mockUser));
    }
    saveUser(mockUser);
    setLoading(false);
  };

  const updateUser = (userData: Partial<AuthUser>) => {
    if (!user) return;
    saveUser(normalizeUser({ ...user, ...userData }));
  };

  const value: AuthContextType = {
    user,
    loading,
    isLoading: loading,
    isAuthenticated: !!user,
    login,
    register,
    loginWithGoogle,
    logout,
    devLogin,
    refreshToken,
    checkAuth,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
