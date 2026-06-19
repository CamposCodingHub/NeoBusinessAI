import path from 'node:path';
import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

const fixture = path.resolve(
  '..',
  'backend',
  'runtime',
  'stress_documents',
  'atlas_250_paginas.pdf'
);

test('fila visual persiste enquanto o usuario navega entre paginas', async ({
  page,
  request,
}) => {
  test.setTimeout(600000);

  await authenticatePage(page, request);
  await page.goto('/dashboard/documents');
  await page.locator('#file-input').setInputFiles(fixture);
  await page.getByRole('button', { name: /fazer upload/i }).click();
  await expect(page.getByText('atlas_250_paginas.pdf')).toBeVisible({
    timeout: 60000,
  });

  await page.getByRole('button', { name: /^analisar$/i }).first().click();
  await expect(page.getByText(/documento enviado para a fila/i)).toBeVisible();
  await expect(page.getByText(/na fila|processando/i).first()).toBeVisible();
  await expect(page.getByRole('button', { name: /excluir/i }).first()).toBeDisabled();

  await page.getByRole('link', { name: /voltar/i }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.goto('/dashboard/documents');

  await expect(page.getByText('atlas_250_paginas.pdf')).toBeVisible();
  await expect(page.getByText(/concluido/i).first()).toBeVisible({
    timeout: 300000,
  });
  await page.getByRole('button', { name: /ver resultado/i }).click();
  await expect(page.getByTestId('document-result-modal')).toBeVisible();
  await expect(page.getByText(/resultado da analise/i)).toBeVisible();
  await expect(
    page.getByRole('heading', { name: /resumo executivo/i })
  ).toBeVisible();
  await page.getByRole('button', { name: /fechar/i }).click();

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: /excluir/i }).first().click();
  await expect(page.getByText('atlas_250_paginas.pdf')).toHaveCount(0, {
    timeout: 60000,
  });
});
