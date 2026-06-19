import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

test.describe('dashboard', () => {
  test.beforeEach(async ({ page, request }) => {
    await authenticatePage(page, request);
  });

  test('renderiza resumo principal e acoes rapidas', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.getByRole('button', { name: /controle de prazos/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /upload documento/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /relat/i })).toBeVisible();
  });

  test('navega para a central de relatorios e abre preview de artefato', async ({ page }) => {
    await page.goto('/dashboard');
    await page.getByRole('button', { name: /relat/i }).click();
    await page.waitForURL(/\/dashboard\/reports/, { timeout: 20000 });

    await expect(page.locator('h1')).toContainText(/relatorios, simulacoes/i);
    await expect(page.locator('text=Acervo de artefatos')).toBeVisible();
    await expect(page.locator('text=Preview tecnico')).toBeVisible();

    const artifactButtons = page.locator('button').filter({ hasText: '.md' });
    if (await artifactButtons.count()) {
      await artifactButtons.first().click();
      await expect(page.locator('pre').last()).toBeVisible();
    }
  });

  test('navega para chat e documentos a partir do dashboard', async ({ page }) => {
    await page.goto('/dashboard');

    await page.getByRole('button', { name: /chat/i }).click();
    await page.waitForURL(/\/chat/, { timeout: 20000 });
    await expect(page.locator('textarea')).toBeVisible();

    await page.goto('/dashboard');
    await page.getByRole('button', { name: /upload documento/i }).click();
    await page.waitForURL(/\/dashboard\/documents/, { timeout: 20000 });
    await expect(page.locator('h1')).toContainText('Documentos');
    await expect(page.locator('#file-input')).toBeAttached();
  });
});
