import type { APIRequestContext, APIResponse, Page } from '@playwright/test';

const BACKEND_URL = process.env.E2E_API_URL || 'http://127.0.0.1:8000';

export interface TestIdentity {
  email: string;
  password: string;
  name: string;
}

export function createTestIdentity(prefix = 'playwright'): TestIdentity {
  const suffix = `${Date.now()}_${Math.floor(Math.random() * 100000)}`;
  return {
    email: `${prefix}_${suffix}@example.com`,
    password: 'SenhaForte123!',
    name: `Usuario ${prefix} ${suffix}`,
  };
}

async function parseError(response: APIResponse): Promise<string> {
  try {
    return await response.text();
  } catch {
    return `HTTP ${response.status()}`;
  }
}

export async function registerViaApi(
  request: APIRequestContext,
  identity: TestIdentity
): Promise<void> {
  const response = await request.post(`${BACKEND_URL}/auth/register`, {
    data: {
      email: identity.email,
      password: identity.password,
      name: identity.name,
    },
  });

  if (!response.ok()) {
    throw new Error(`Falha ao registrar usuario de teste: ${await parseError(response)}`);
  }
}

export async function loginViaApi(
  request: APIRequestContext,
  identity: TestIdentity
): Promise<{
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: Record<string, unknown>;
}> {
  const response = await request.post(`${BACKEND_URL}/auth/login`, {
    data: {
      email: identity.email,
      password: identity.password,
    },
  });

  if (!response.ok()) {
    throw new Error(`Falha ao autenticar usuario de teste: ${await parseError(response)}`);
  }

  return (await response.json()) as {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: Record<string, unknown>;
  };
}

export async function authenticatePage(
  page: Page,
  request: APIRequestContext,
  identity?: TestIdentity
): Promise<TestIdentity> {
  const nextIdentity = identity || createTestIdentity();
  await registerViaApi(request, nextIdentity);
  const session = await loginViaApi(request, nextIdentity);

  await page.addInitScript(({ tokens, user }) => {
    localStorage.setItem(
      'neobusiness_tokens',
      JSON.stringify({
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        token_type: tokens.token_type || 'bearer',
      })
    );
    localStorage.setItem('neobusiness_user', JSON.stringify(user));
    localStorage.setItem('onboarding_completed', 'true');
  }, { tokens: session, user: session.user });

  const authCheck = page.waitForResponse(
    (response) =>
      response.url().endsWith('/auth/me') &&
      response.request().method() === 'GET',
    { timeout: 30000 }
  );
  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
  const authResponse = await authCheck;
  if (!authResponse.ok()) {
    throw new Error(
      `Sessao visual nao foi validada: HTTP ${authResponse.status()} em /auth/me`
    );
  }
  await page.locator('h1', { hasText: 'Dashboard' }).waitFor({
    state: 'visible',
    timeout: 30000,
  });

  return nextIdentity;
}
