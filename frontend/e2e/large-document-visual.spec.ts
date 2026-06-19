import path from 'node:path';
import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

const fixture = (name: string) =>
  path.resolve('..', 'backend', 'runtime', 'stress_documents', name);

test('documentos extremos visuais: 12MB, limite e assinatura falsa', async ({
  page,
  request,
}) => {
  test.setTimeout(900000);

  await authenticatePage(page, request);
  await page.goto('/dashboard/documents');

  await test.step('upload e analise do TXT de 12MB', async () => {
    await page.locator('#file-input').setInputFiles(fixture('atlas_12mb.txt'));
    await expect(page.locator('text=Arquivo selecionado: atlas_12mb.txt')).toBeVisible();
    await page.getByRole('button', { name: /fazer upload/i }).click();
    await expect(page.getByText('atlas_12mb.txt')).toBeVisible({ timeout: 120000 });

    await page.getByRole('button', { name: /analisar/i }).first().click();
    await expect(page.getByText(/documento enviado para a fila/i)).toBeVisible({
      timeout: 20000,
    });
    await expect(page.getByText(/na fila|processando/i).first()).toBeVisible({
      timeout: 20000,
    });
    await expect(
      page.getByText('Analise concluida e documento atualizado.')
    ).toBeVisible({ timeout: 300000 });

    page.once('dialog', (dialog) => dialog.accept());
    await page.getByRole('button', { name: /excluir/i }).first().click();
    await expect(page.getByText('atlas_12mb.txt')).toHaveCount(0, {
      timeout: 60000,
    });
  });

  await test.step('bloqueio no navegador para arquivo de 51MB', async () => {
    await page
      .locator('#file-input')
      .setInputFiles(fixture('acima_limite_51mb.txt'));
    await expect(page.getByText(/limite atual e 50MB/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /fazer upload/i })).toBeDisabled();
  });

  await test.step('rejeicao no servidor para PDF disfarçado', async () => {
    await page
      .locator('#file-input')
      .setInputFiles(fixture('executavel_disfarcado.pdf'));
    await page.getByRole('button', { name: /fazer upload/i }).click();
    await expect(
      page.getByText(/conteudo do arquivo nao corresponde a extensao/i)
    ).toBeVisible({ timeout: 60000 });
  });
});
