import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

test.describe('documentos', () => {
  test.beforeEach(async ({ page, request }) => {
    await authenticatePage(page, request);
    await page.goto('/dashboard/documents');
  });

  test('aceita upload de arquivo suportado', async ({ page }) => {
    const documentName = `upload-${Date.now()}.pdf`;

    await page.locator('#file-input').setInputFiles({
      name: documentName,
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 arquivo de teste playwright'),
    });
    await page.getByRole('button', { name: /fazer upload/i }).click();

    await expect(page.locator(`text=${documentName}`)).toBeVisible({ timeout: 20000 });
    await expect(page.locator('text=Documento enviado com sucesso.')).toBeVisible();
  });

  test('bloqueia formato invalido antes do envio', async ({ page }) => {
    await page.locator('#file-input').setInputFiles({
      name: 'malicioso.exe',
      mimeType: 'application/octet-stream',
      buffer: Buffer.from('arquivo invalido'),
    });

    await expect(page.locator('text=Formato nao suportado')).toBeVisible();
    await expect(page.getByRole('button', { name: /fazer upload/i })).toBeDisabled();
  });

  test('analisa e exclui documento enviado', async ({ page }) => {
    const documentName = `analise-${Date.now()}.txt`;

    await page.locator('#file-input').setInputFiles({
      name: documentName,
      mimeType: 'text/plain',
      buffer: Buffer.from(
        'Contrato de servicos. Processo 12345-67.2026.8.26.0001. Prazo de 15 dias. Valor R$ 10.000,00.',
        'utf-8'
      ),
    });
    await page.getByRole('button', { name: /fazer upload/i }).click();
    await expect(page.locator(`text=${documentName}`)).toBeVisible({ timeout: 20000 });

    await page.getByRole('button', { name: /analisar/i }).first().click();
    await expect(
      page.getByText(/documento enviado para a fila/i)
    ).toBeVisible({ timeout: 20000 });
    await expect(page.locator('text=Analise concluida e documento atualizado.')).toBeVisible({
      timeout: 120000,
    });

    page.once('dialog', (dialog) => dialog.accept());
    await page.getByRole('button', { name: /excluir/i }).first().click();
    await expect(page.locator(`text=${documentName}`)).toHaveCount(0, { timeout: 20000 });
  });
});
