// Configuração da API
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Flag para evitar loop infinito de refresh
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

// Fila de requisições pendentes durante refresh
let pendingRequests: Array<(token: string | null) => void> = [];

// Função para processar fila de requisições pendentes
function processPendingRequests(token: string | null) {
  pendingRequests.forEach(callback => callback(token));
  pendingRequests = [];
}

// Função para adicionar requisição à fila
function addPendingRequest(callback: (token: string | null) => void) {
  pendingRequests.push(callback);
}

// Função para renovar o token
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;

  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Refresh failed');
    }

    const data = await response.json();

    // Salvar novo token
    localStorage.setItem('token', data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }

    return data.access_token;
  } catch (error) {
    // Limpar tokens em caso de erro
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login?expired=true';
    return null;
  }
}

// Helper para requisições autenticadas com refresh automático
export async function apiFetch(endpoint: string, options: RequestInit = {}, retryCount = 0): Promise<any> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Merge headers from options
  if (options.headers) {
    const opts = options.headers as Record<string, string>;
    Object.keys(opts).forEach(key => {
      headers[key] = opts[key];
    });
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Token expirado (401)
  if (response.status === 401 && retryCount === 0) {
    // Se já estamos renovando, aguardar
    if (isRefreshing) {
      return new Promise((resolve) => {
        addPendingRequest((newToken) => {
          if (newToken) {
            // Refazer a requisição com novo token
            resolve(apiFetch(endpoint, options, retryCount + 1));
          } else {
            resolve(Promise.reject(new Error('Token refresh failed')));
          }
        });
      });
    }

    // Iniciar processo de renovação
    isRefreshing = true;
    refreshPromise = refreshAccessToken();

    const newToken = await refreshPromise;
    isRefreshing = false;
    refreshPromise = null;

    // Processar fila de requisições pendentes
    processPendingRequests(newToken);

    if (newToken) {
      // Refazer a requisição original com novo token
      return apiFetch(endpoint, options, retryCount + 1);
    } else {
      throw new Error('Authentication failed');
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// Função para login
export async function login(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail);
  }

  const data = await response.json();

  // Salvar tokens
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('user', JSON.stringify(data.user));

  return data;
}

// Função para logout
export async function logout() {
  const token = localStorage.getItem('token');

  // Notificar backend sobre logout (opcional)
  if (token) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    } catch (e) {
      // Ignorar erros no logout
    }
  }

  // Limpar storage
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');

  window.location.href = '/login';
}

// Verificar se usuário está autenticado
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('token');
}

// Obter usuário atual
export function getCurrentUser() {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}
