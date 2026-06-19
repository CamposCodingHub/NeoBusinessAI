import path from 'node:path';
import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

const fixture = path.resolve(
  '..',
  'backend',
  'runtime',
  'stress_documents',
  'acima_limite_501_paginas.pdf'
);

test('falha assincrona fica explicita e permite nova tentativa', async ({
  page,
  request,
}) => {
  test.setTimeout(600000);

  await authenticatePage(page, request);
  await page.goto('/dashboard/documents');
  await page.locator('#file-input').setInputFiles(fixture);
  await page.getByRole('button', { name: /fazer upload/i }).click();
  await expect(page.getByText('acima_limite_501_paginas.pdf')).toBeVisible();

  await page.getByRole('button', { name: /^analisar$/i }).click();
  await expect(page.getByText(/documento enviado para a fila/i)).toBeVisible();
  await expect(page.getByText(/limite seguro: 500/i).first()).toBeVisible({
    timeout: 120000,
  });
  await expect(
    page.getByRole('button', { name: /tentar novamente/i })
  ).toBeVisible();

  await page.getByRole('button', { name: /tentar novamente/i }).click();
  await expect(page.getByText(/documento enviado para a fila/i)).toBeVisible();
  await expect(page.getByText(/limite seguro: 500/i).first()).toBeVisible({
    timeout: 120000,
  });

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: /excluir/i }).click();
  await expect(page.getByText('acima_limite_501_paginas.pdf')).toHaveCount(0);
});
