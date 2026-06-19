import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

test('pesquisa juridica visual: CDC, evidencias e continuidade', async ({
  page,
  request,
}) => {
  test.setTimeout(480000);

  await authenticatePage(page, request);
  await page.goto('/chat');

  await page.getByRole('button', { name: /pesquisa profunda/i }).click();

  const firstAssistantCount = await page
    .getByTestId('chat-message-assistant')
    .count();
  await page.locator('textarea').fill(
    'Diferencie vicio e fato do produto no CDC. Cite os artigos 12, 18, 26 e 27, explique os prazos de 30 e 90 dias e nao invente jurisprudencia.'
  );
  await page.getByRole('button', { name: /enviar/i }).click();

  await expect(page.getByTestId('chat-message-assistant')).toHaveCount(
    firstAssistantCount + 1,
    { timeout: 180000 }
  );

  const firstAnswer = page.getByTestId('chat-message-assistant').last();
  const firstAnswerText = await firstAnswer.innerText();
  if (/nao pode ser concluida/i.test(firstAnswerText)) {
    await expect(firstAnswer).toContainText(/nenhuma conclusao juridica foi gerada/i);
    await firstAnswer
      .getByText(/ver evidencia normativa recuperada/i)
      .click();
    await expect(firstAnswer).toContainText(/Art\. 12/i);
    await expect(page.locator('body')).toContainText(/contingencia, revisar/i);

    await page.goto('/dashboard');
    await page.goto('/chat');
    await expect(page.getByTestId('chat-message-user')).toHaveCount(1);
    return;
  }

  await expect(firstAnswer).toContainText(/art(?:igo)?\.?\s*26/i);
  await expect(firstAnswer).toContainText(/30 dias/i);
  await expect(firstAnswer).toContainText(/90 dias/i);
  await expect(firstAnswer).toContainText(/Fonte 1/i);
  await expect(firstAnswer).not.toContainText(/180 dias/i);

  await firstAnswer
    .getByText(/ver evidencia normativa recuperada/i)
    .click();
  await expect(firstAnswer).toContainText(/Art\. 12/i);

  await page.getByRole('button', { name: /consulta rapida/i }).click();
  const followUpAssistantCount = await page
    .getByTestId('chat-message-assistant')
    .count();
  await page.locator('textarea').fill(
    'Mantendo esse contexto: em um produto duravel com vicio oculto, quando comeca o prazo e qual prazo deve ser conferido?'
  );
  await page.getByRole('button', { name: /enviar/i }).click();

  await expect(page.getByTestId('chat-message-assistant')).toHaveCount(
    followUpAssistantCount + 1,
    { timeout: 180000 }
  );
  const followUpAnswer = page.getByTestId('chat-message-assistant').last();
  await expect(followUpAnswer).toContainText(/90 dias/i);
  await expect(followUpAnswer).toContainText(/art(?:igo)?\.?\s*26/i);
  await expect(followUpAnswer).toContainText(
    /evidente|evidenciado|conhecimento|descoberta/i
  );

  await expect(page.locator('body')).toContainText(/Artigos verificados/i);
  await expect(page.locator('body')).toContainText(
    /modelo solicitado concluido|motor robusto alternativo|contingencia, revisar/i
  );

  await page.goto('/dashboard');
  await page.goto('/chat');
  await expect(page.getByTestId('chat-message-user')).toHaveCount(2);
  await expect(page.locator('body')).toContainText(/produto duravel com vicio oculto/i);
});
