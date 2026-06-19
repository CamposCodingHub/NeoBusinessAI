import { expect, test } from '@playwright/test';

test('simulador visual percorre modulos e botoes principais', async ({ page }) => {
  test.setTimeout(180000);

  await page.goto('/simulador?presentation=1');

  await expect(
    page.getByRole('heading', {
      name: /Ambiente interativo para encenar a operacao completa do NeoBusiness AI/i,
    }),
  ).toBeVisible();

  await expect(page.getByText(/Demonstracao guiada ativada/i)).toBeVisible();

  await page.getByRole('button', { name: /Executar simulacao completa/i }).click();
  await expect(page.getByText(/Apresentacao concluida com sucesso\./i)).toBeVisible({
    timeout: 90000,
  });
  await page.waitForTimeout(1200);

  await page.locator('button').filter({ hasText: 'Documentos' }).first().click();
  await page.waitForTimeout(700);
  await page.getByRole('button', { name: /Simular upload/i }).click();
  await page.waitForTimeout(900);

  await page.locator('button').filter({ hasText: 'Clientes' }).first().click();
  await page.waitForTimeout(700);
  await page.getByRole('button', { name: /Cadastrar lead/i }).click();
  await page.waitForTimeout(900);

  await page.locator('button').filter({ hasText: 'Financeiro' }).first().click();
  await page.waitForTimeout(700);
  await page.getByRole('button', { name: /Gerar fatura/i }).click();
  await page.waitForTimeout(900);

  await page.locator('button').filter({ hasText: 'Chat IA' }).first().click();
  await page.waitForTimeout(700);
  await page.getByRole('button', { name: /Pergunta sobre prazos/i }).click();
  await page.waitForTimeout(1200);

  await expect(page.getByText(/Pergunta enviada ao copiloto/i).first()).toBeVisible();
});
