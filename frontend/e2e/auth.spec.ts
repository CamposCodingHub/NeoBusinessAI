import { expect, test } from '@playwright/test';
import { createTestIdentity } from './helpers';

test.describe('autenticacao', () => {
  test('login e registro carregam corretamente', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText(/bem-vindo/i);

    await page.getByRole('link', { name: /criar conta/i }).click();
    await expect(page).toHaveURL(/\/register/);
    await expect(page.locator('h2')).toContainText(/crie sua conta/i);
  });

  test('login invalido exibe feedback claro', async ({ page }) => {
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('naoexiste@example.com');
    await page.locator('input[type="password"]').fill('senha-invalida');
    await page.getByRole('button', { name: /^entrar$/i }).click();

    await expect(page.locator('text=Erro HTTP 401')).toBeVisible();
  });

  test('cadastro via interface leva ao onboarding e permite novo login', async ({ page }) => {
    const identity = createTestIdentity('auth_ui');

    await page.goto('/register');
    await page.locator('input[type="email"]').fill(identity.email);
    await page.locator('input[type="password"]').nth(0).fill(identity.password);
    await page.locator('input[type="password"]').nth(1).fill(identity.password);
    await page.getByRole('button', { name: /continuar/i }).click();

    await page.locator('input[type="text"]').nth(0).fill(identity.name);
    await page.locator('input[type="text"]').nth(1).fill('Escritorio Auth UI');
    await page.getByRole('button', { name: /advogado aut/i }).click();
    await page.getByRole('button', { name: /ver planos/i }).click();

    await page.locator('input[type="checkbox"]').check();
    await page.getByRole('button', { name: /come/i }).click();
    await page.waitForURL(/\/onboarding/, { timeout: 30000 });

    await page.getByRole('button', { name: /come.*jornada/i }).click();
    await page.getByRole('button', { name: /c.vel/i }).click();
    await page.getByRole('button', { name: /continuar/i }).click();
    await page.getByRole('button', { name: /acessar plataforma/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 30000 });
    await expect(page.locator('h1')).toContainText('Dashboard');

    await page.getByRole('button', { name: /sair/i }).click();
    await page.waitForURL(/\/login/, { timeout: 20000 });

    await page.locator('input[type="email"]').fill(identity.email);
    await page.locator('input[type="password"]').fill(identity.password);
    await page.getByRole('button', { name: /^entrar$/i }).click();
    await page.waitForURL(/\/dashboard|\/onboarding/, { timeout: 30000 });
  });
});
