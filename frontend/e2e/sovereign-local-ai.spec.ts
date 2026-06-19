import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

test('IA soberana local responde com base normativa e auditoria visual', async ({
  page,
  request,
}) => {
  test.setTimeout(720000);

  await authenticatePage(page, request);
  await page.goto('/chat');

  await expect(page.getByText('IA soberana local')).toBeVisible({
    timeout: 30000,
  });
  await expect(page.getByText('Motor soberano online')).toBeVisible();
  await expect(page.locator('body')).toContainText('lex-juridica-instant:1.5b');

  await page.getByRole('button', { name: /consulta rapida/i }).click();
  const assistantCount = await page
    .getByTestId('chat-message-assistant')
    .count();
  await page.locator('textarea').fill(
    'Explique os requisitos do artigo 312 do Codigo de Processo Penal para a prisao preventiva. Diferencie prova da existencia do crime, indicio suficiente de autoria e perigo gerado pela liberdade. Cite apenas fontes recuperadas.'
  );
  await page.getByRole('button', { name: /enviar/i }).click();

  await expect(page.getByTestId('chat-message-assistant')).toHaveCount(
    assistantCount + 1,
    { timeout: 600000 }
  );

  const answer = page.getByTestId('chat-message-assistant').last();
  await expect(answer).toContainText(/Base normativa verificada/i);
  await expect(answer).toContainText(/prova da exist.ncia do crime/i);
  await expect(answer).toContainText(/ind.cio suficiente de autoria/i);
  await expect(answer).toContainText(/perigo gerado.*liberdade/i);
  await expect(answer).toContainText(/Fonte 1/i);
  await expect(answer).not.toContainText(/Fonte [2-9]/i);
  await expect(answer).not.toContainText(/motor juridico alternativo/i);
  await expect(answer).not.toContainText(
    /ind.cio suficiente de autoria.{0,120}artigo 315|artigo 315.{0,120}ind.cio suficiente de autoria/i
  );

  await expect(page.locator('body')).toContainText(
    'Provedor: local-knowledge-engine'
  );
  await expect(page.locator('body')).toContainText(
    'Modelo: lex-retrieval-verificada'
  );
  await expect(page.locator('body')).toContainText('Base local: consultada');
  await expect(page.locator('body')).toContainText(
    'Execucao: modelo solicitado concluido'
  );
  await expect(page.locator('body')).toContainText(
    'Fontes invalidas bloqueadas:'
  );
  await expect(page.locator('body')).toContainText(
    'Associacoes normativas bloqueadas:'
  );

  await page.screenshot({
    path: '../relatorios_melhorias/simulacoes/ia-soberana-visual-final.png',
    fullPage: true,
  });
});
