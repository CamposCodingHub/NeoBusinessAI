import { expect, test } from '@playwright/test';

test('critical path: register, onboarding, modules, upload and AI chat', async ({
  page,
}) => {
  const uniqueId = Date.now();
  const email = `playwright_${uniqueId}@example.com`;
  const password = 'SenhaForte123!';
  const clientName = `Cliente PW ${uniqueId}`;
  const deadlineName = `Prazo PW ${uniqueId}`;
  const invoiceName = `Fatura PW ${uniqueId}`;
  const documentName = `contrato-pw-${uniqueId}.txt`;

  await test.step('landing and legal pages load', async () => {
    await page.goto('/');
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('link', { name: /neoBusiness ai/i }).first()).toBeVisible();

    await page.goto('/terms');
    await expect(page.locator('h1')).toContainText('Termos');

    await page.goto('/privacy');
    await expect(page.locator('h1')).toContainText('Privacidade');
  });

  await test.step('register a new user', async () => {
    await page.goto('/register');

    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').nth(0).fill(password);
    await page.locator('input[type="password"]').nth(1).fill(password);
    await page.getByRole('button', { name: /continuar/i }).click();

    await page.locator('input[type="text"]').nth(0).fill('Playwright Teste');
    await page.locator('input[type="text"]').nth(1).fill('Escritorio PW');
    await page.getByRole('button', { name: /advogado aut/i }).click();
    await page.getByRole('button', { name: /ver planos/i }).click();

    await page.locator('input[type="checkbox"]').check();
    await page.getByRole('button', { name: /come.*gr[aá]tis/i }).click();
    await page.waitForURL(/\/onboarding/, { timeout: 30000 });
  });

  await test.step('finish onboarding', async () => {
    await page.getByRole('button', { name: /come.*jornada/i }).click();
    await page.getByRole('button', { name: /c[ií]vel/i }).click();
    await page.getByRole('button', { name: /continuar/i }).click();
    await page.getByRole('button', { name: /acessar plataforma/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 30000 });
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  await test.step('create a deadline', async () => {
    await page.locator('a[href="/dashboard/deadlines"]').first().click();
    await page.waitForURL(/\/dashboard\/deadlines/);

    await page.getByRole('button', { name: /\+ novo prazo/i }).click();
    const deadlineForm = page.locator('form').filter({ hasText: /Criar Prazo/i }).first();
    await deadlineForm.locator('input[placeholder*="Responder"]').fill(deadlineName);
    await deadlineForm.locator('input[placeholder*="Processo"]').fill('Processo PW-001');
    await deadlineForm.getByRole('button', { name: /criar prazo/i }).click();

    await expect(page.locator(`text=${deadlineName}`)).toBeVisible();
  });

  await test.step('create a client and open details page', async () => {
    await page.goto('/dashboard/clients');
    await page.getByRole('button', { name: /\+ novo cliente/i }).click();

    const clientForm = page.locator('form').filter({ hasText: /Criar Cliente/i }).first();
    await clientForm.locator('input').nth(0).fill(clientName);
    await clientForm.locator('input[type="email"]').fill(`cliente_${uniqueId}@example.com`);
    await clientForm.locator('input').nth(2).fill('11999999999');
    await clientForm.locator('input').nth(3).fill('12345678900');
    await clientForm.locator('input').nth(4).fill('Rua Playwright, 100');
    await clientForm.locator('input').nth(5).fill('Sao Paulo');
    await clientForm.locator('input').nth(6).fill('SP');
    await clientForm.locator('textarea').fill('Cliente criado no fluxo automatizado.');
    await clientForm.getByRole('button', { name: /criar cliente/i }).click();

    await expect(page.locator(`text=${clientName}`)).toBeVisible();
    await page.getByRole('link', { name: /detalhes/i }).first().click();
    await page.waitForURL(/\/dashboard\/clients\/\d+/, { timeout: 20000 });
    await expect(page.locator('h1')).toContainText(clientName);
  });

  await test.step('create an invoice', async () => {
    await page.goto('/dashboard/finance');
    await page.getByRole('button', { name: /\+ nova fatura/i }).click();

    const invoiceForm = page.locator('form').filter({ hasText: /Criar Fatura/i }).first();
    await invoiceForm.locator('input[placeholder*="Honor"]').fill(invoiceName);
    await invoiceForm.locator('input[type="number"]').nth(0).fill('1500');
    await invoiceForm.locator('input[type="number"]').nth(1).fill('0');
    await invoiceForm.locator('input[type="number"]').nth(2).fill('7');
    await invoiceForm.getByRole('button', { name: /criar fatura/i }).click();

    await expect(page.locator(`text=${invoiceName}`)).toBeVisible();
  });

  await test.step('upload and analyze a document', async () => {
    await page.goto('/dashboard/documents');
    await page.locator('#file-input').setInputFiles({
      name: documentName,
      mimeType: 'text/plain',
      buffer: Buffer.from(
        'Contrato de prestacao de servicos. Prazo de 15 dias. Valor R$ 5.000,00.',
        'utf-8'
      ),
    });
    await page.getByRole('button', { name: /fazer upload/i }).click();

    await expect(page.locator(`text=${documentName}`)).toBeVisible();

    const uploadedDocumentCard = page
      .getByTestId('documents-list')
      .locator(':scope > div')
      .filter({ hasText: documentName })
      .first();
    const analyzeButton = uploadedDocumentCard.getByRole('button', {
      name: /analisar/i,
    });
    if (await analyzeButton.isVisible().catch(() => false)) {
      await analyzeButton.click();
      await expect(
        page.getByText('Analise concluida e documento atualizado.')
      ).toBeVisible({ timeout: 120000 });
    }
  });

  await test.step('chat with AI', async () => {
    await page.goto('/chat');

    await page.locator('textarea').fill('Monte um checklist para revisar um contrato de prestacao de servicos.');
    await page.getByRole('button', { name: /enviar/i }).click();

    await expect(page.locator('textarea')).toHaveValue('');

    await expect
      .poll(async () => {
        const allText = await page.locator('body').textContent();
        return allText || '';
      }, { timeout: 45000 })
      .toContain('contrato');
  });

  await test.step('logout and login again', async () => {
    await page.goto('/dashboard');
    await page.getByRole('button', { name: /sair/i }).click();
    await page.waitForURL(/\/login/, { timeout: 20000 });

    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(password);
    await page.getByRole('button', { name: /^entrar$/i }).click();
    await page.waitForURL(/\/dashboard|\/onboarding/, { timeout: 30000 });
  });
});
