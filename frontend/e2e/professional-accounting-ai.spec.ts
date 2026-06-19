import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

test('IA profissional visual: DCTFWeb, memoria e contingencia detalhada', async ({
  page,
  request,
}) => {
  test.setTimeout(600000);

  await authenticatePage(page, request);
  await page.goto('/chat');
  await page.getByRole('button', { name: /pesquisa profunda/i }).click();

  const prompts = [
    (
      'Caso Aurora: empregado Marcos, salario de R$ 8.400,00 e admissao em ' +
      '12/03/2022. Explique como revisar desligamento no eSocial e conciliacao ' +
      'posterior com DCTFWeb e DARF, com fontes oficiais e revisao humana.'
    ),
    (
      'Retome o caso Aurora: qual empregado, salario e data de admissao foram ' +
      'informados? Depois monte uma matriz RACI entre advogado, contador, RH e diretoria.'
    ),
  ];

  for (const prompt of prompts) {
    const assistantCount = await page
      .getByTestId('chat-message-assistant')
      .count();
    await page.locator('textarea').fill(prompt);
    await page.getByRole('button', { name: /enviar/i }).click();
    await expect(page.getByTestId('chat-message-assistant')).toHaveCount(
      assistantCount + 1,
      { timeout: 240000 }
    );
  }

  const finalAnswer = page.getByTestId('chat-message-assistant').last();
  await expect(finalAnswer).toContainText(/Marcos/i);
  await expect(finalAnswer).toContainText(/8\.400|8400/i);
  await expect(finalAnswer).toContainText(/12\/03\/2022/i);
  await expect(finalAnswer).toContainText(/advogado/i);
  await expect(finalAnswer).toContainText(/contador/i);
  await expect(finalAnswer).toContainText(/RH/i);
  await expect(finalAnswer).toContainText(/diretoria/i);
  await expect(page.locator('body')).toContainText(/Fonte 1/i);
});
