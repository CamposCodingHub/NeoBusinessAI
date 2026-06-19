import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';
import { authenticatePage } from './helpers';

const fixture = (name: string) =>
  path.resolve('..', 'backend', 'runtime', 'stress_documents', name);

async function accessToken(page: Page): Promise<string> {
  return page.evaluate(() => {
    const raw = localStorage.getItem('neobusiness_tokens');
    return raw ? JSON.parse(raw).access_token : '';
  });
}

async function openModule(
  page: Page,
  pathname: string,
  readyLocator: ReturnType<Page['locator']>
): Promise<void> {
  await page.goto(pathname, { waitUntil: 'domcontentloaded' });
  await page.waitForURL((url) => url.pathname === pathname, {
    timeout: 30000,
  });
  await readyLocator.waitFor({ state: 'visible', timeout: 30000 });
}

test('homologacao completa de usuario ativo, documentos, relatorios e IA', async ({
  page,
  request,
}) => {
  test.setTimeout(1500000);
  const suffix = Date.now();
  const clientName = `Empresa Homologacao ${suffix}`;
  const deadlineName = `Prazo Homologacao ${suffix}`;
  const invoiceName = `Honorarios Homologacao ${suffix}`;
  const contractName = `contrato-homologacao-${suffix}.txt`;

  await authenticatePage(page, request);

  await test.step('criar cliente, prazo e fatura como usuario ativo', async () => {
    const newClientButton = page.getByRole('button', {
      name: /\+ novo cliente/i,
    });
    await openModule(page, '/dashboard/clients', newClientButton);
    await newClientButton.click();
    await expect(
      page.getByRole('heading', { name: /novo cliente/i })
    ).toBeVisible();
    const clientForm = page.locator('form').first();
    await expect(clientForm).toBeVisible();
    await clientForm.locator('input').nth(0).fill(clientName);
    await clientForm
      .locator('input[type="email"]')
      .fill(`juridico_${suffix}@example.com`);
    await clientForm.locator('input').nth(2).fill('11999990000');
    await clientForm.locator('input').nth(3).fill('12345678000190');
    await clientForm.locator('input').nth(4).fill('Avenida Central, 900');
    await clientForm.locator('input').nth(5).fill('Sao Paulo');
    await clientForm.locator('input').nth(6).fill('SP');
    await clientForm.locator('textarea').fill(
      'Cliente criado durante homologacao integral do produto.'
    );
    await clientForm.getByRole('button', { name: /criar cliente/i }).click();
    await expect(page.getByText(clientName)).toBeVisible();

    const newDeadlineButton = page.getByRole('button', {
      name: /\+ novo prazo/i,
    });
    await openModule(page, '/dashboard/deadlines', newDeadlineButton);
    await newDeadlineButton.click();
    await expect(
      page.getByRole('heading', { name: /novo prazo/i })
    ).toBeVisible();
    const deadlineForm = page.locator('form').first();
    await expect(deadlineForm).toBeVisible();
    await deadlineForm
      .locator('input[placeholder*="Responder"]')
      .fill(deadlineName);
    await deadlineForm.locator('input[type="number"]').fill('5');
    await deadlineForm
      .locator('input[placeholder*="Processo"]')
      .fill('Processo HOM-2026-001');
    await deadlineForm.getByRole('button', { name: /criar prazo/i }).click();
    await expect(page.getByText(deadlineName)).toBeVisible();

    const newInvoiceButton = page.getByRole('button', {
      name: /\+ nova fatura/i,
    });
    await openModule(page, '/dashboard/finance', newInvoiceButton);
    await newInvoiceButton.click();
    await expect(
      page.getByRole('heading', { name: /nova fatura/i })
    ).toBeVisible();
    const invoiceForm = page.locator('form').first();
    await expect(invoiceForm).toBeVisible();
    await invoiceForm
      .locator('input[placeholder*="Honor"]')
      .fill(invoiceName);
    await invoiceForm.locator('input[type="number"]').nth(0).fill('4800');
    await invoiceForm.locator('input[type="number"]').nth(1).fill('300');
    await invoiceForm.locator('input[type="number"]').nth(2).fill('10');
    await invoiceForm.getByRole('button', { name: /criar fatura/i }).click();
    await expect(page.getByText(invoiceName)).toBeVisible();
  });

  await test.step('gerar e renderizar uma peca juridica', async () => {
    const select = page.locator('select');
    await openModule(page, '/dashboard/legal', select);
    await expect(select.locator('option')).toHaveCount(7, {
      timeout: 30000,
    });
    await select.selectOption('peticao_inicial');
    const textareas = page.locator('form textarea');
    await textareas.nth(0).fill(
      `${clientName} contra Fornecedora Delta Ltda.`
    );
    await textareas.nth(1).fill(
      'Inadimplemento contratual após notificacao e ausencia de correcao.'
    );
    await textareas.nth(2).fill(
      'Cumprimento da obrigacao, perdas e danos e tutela adequada.'
    );
    await textareas.nth(3).fill(
      'Minuta produzida apenas para revisao profissional.'
    );
    await page.getByRole('button', { name: /gerar pe/i }).click();
    await expect(
      page.getByRole('heading', { name: 'Peticao Inicial', exact: true })
    ).toBeVisible({ timeout: 30000 });
  });

  const files = [
    {
      name: contractName,
      input: {
        name: contractName,
        mimeType: 'text/plain',
        buffer: Buffer.from(
          [
            'CONTRATO OPERACAO ORION.',
            `Contratante: ${clientName}.`,
            'Contratada: Solucoes Delta Ltda.',
            'Valor mensal: R$ 24.500,00.',
            'Vigencia: 18 meses.',
            'Aviso previo: 45 dias.',
            'Multa: duas mensalidades.',
            'Correcao de inadimplemento: 10 dias.',
            'Incidente LGPD: comunicar em 24 horas.',
            'Risco: anexo de nivel de servico sem disponibilidade minima.',
          ].join('\n'),
          'utf-8'
        ),
      },
    },
    {
      name: 'atlas_9000_paragrafos.docx',
      input: fixture('atlas_9000_paragrafos.docx'),
    },
    {
      name: 'atlas_250_paginas.pdf',
      input: fixture('atlas_250_paginas.pdf'),
    },
  ];

  await test.step('enviar, analisar e abrir tres arquivos diferentes', async () => {
    await openModule(
      page,
      '/dashboard/documents',
      page.locator('label[for="file-input"]')
    );

    for (const file of files) {
      await page.locator('#file-input').setInputFiles(file.input);
      await page.getByRole('button', { name: /fazer upload/i }).click();
      await expect(page.getByText(file.name)).toBeVisible({ timeout: 60000 });

      const card = page
        .getByTestId('documents-list')
        .locator(':scope > div')
        .filter({ hasText: file.name })
        .first();
      await card.getByRole('button', { name: /^analisar$/i }).click();
      await expect(card).toContainText(/Concluido/i, { timeout: 360000 });

      await card.getByRole('button', { name: /ver resultado/i }).click();
      const modal = page.getByTestId('document-result-modal');
      await expect(modal).toBeVisible();
      await expect(modal).toContainText(/Resumo executivo/i);
      await expect(modal).not.toContainText(/Resumo nao disponivel/i);
      await expect(modal).toContainText(/Analise profissional/i);
      await modal.getByRole('button', { name: /fechar/i }).click();
    }
  });

  await test.step('validar dados persistidos e central de relatorios', async () => {
    const token = await accessToken(page);
    const documentsResponse = await request.get(
      'http://127.0.0.1:8000/documents/?limit=100',
      { headers: { Authorization: `Bearer ${token}` } }
    );
    expect(documentsResponse.ok()).toBeTruthy();
    const documentsPayload = await documentsResponse.json();
    const testedDocuments = documentsPayload.documents.filter(
      (document: { filename: string }) =>
        files.some((file) => file.name === document.filename)
    );
    expect(testedDocuments).toHaveLength(3);
    expect(
      testedDocuments.every(
        (document: { status: string }) => document.status === 'completed'
      )
    ).toBeTruthy();

    for (const document of testedDocuments) {
      const detailResponse = await request.get(
        `http://127.0.0.1:8000/documents/${document.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const detail = await detailResponse.json();
      expect(String(detail.summary || '').length).toBeGreaterThan(20);
      expect(String(detail.analysis || '').length).toBeGreaterThan(20);
    }

    const reportsResponse = await request.get(
      'http://127.0.0.1:8000/operations/reports-center',
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const reports = await reportsResponse.json();
    expect(reports.overview.workspace.documents.completed).toBeGreaterThanOrEqual(
      3
    );
    expect(reports.overview.workspace.clients.active).toBeGreaterThanOrEqual(1);
    expect(reports.overview.workspace.finance.open_total).toBeGreaterThan(0);
    expect(reports.summary_markdown).toMatch(/Resumo (Executivo|Operacional)/);

    await openModule(
      page,
      '/dashboard/reports',
      page.getByText('Resumo em Markdown')
    );
    await expect(page.locator('h1')).toContainText(/relatorios, simulacoes/i);
    await expect(page.getByText('Resumo em Markdown')).toBeVisible();
    await expect(page.getByText('Acervo de artefatos')).toBeVisible();
    await page.screenshot({
      path: '../relatorios_melhorias/simulacoes/homologacao-relatorios.png',
      fullPage: true,
    });
  });

  await test.step('conversa prolongada com tres arquivos e pesquisa atual', async () => {
    const documentSelect = page.getByRole('listbox', {
      name: /documento em contexto/i,
    });
    await openModule(page, '/chat', documentSelect);
    await documentSelect.selectOption(
      files.map((file) => ({ label: file.name }))
    );
    await expect(page.getByTestId('document-context-status')).toContainText(
      '3 documento(s)'
    );
    await page.getByRole('button', { name: /consulta rapida/i }).click();

    const evidencePrompts = [
      'Resuma os tres arquivos selecionados separadamente.',
      'Liste as partes identificadas em cada documento.',
      'Quais prazos e vigencias foram extraidos dos arquivos?',
      'Quais valores, multas e riscos aparecem nos documentos?',
      'Monte uma visao consolidada das evidencias dos arquivos, sem inventar dados.',
    ];

    for (const prompt of evidencePrompts) {
      const assistantCount = await page
        .getByTestId('chat-message-assistant')
        .count();
      await page.locator('textarea').fill(prompt);
      await page.getByRole('button', { name: /enviar/i }).click();
      await expect(page.getByTestId('chat-message-assistant')).toHaveCount(
        assistantCount + 1,
        { timeout: 90000 }
      );
      await expect(page.getByTestId('chat-message-assistant').last()).toContainText(
        /Evidencias dos documentos selecionados/i
      );
    }

    await page.getByRole('button', { name: /consulta rapida/i }).click();
    const currentCount = await page
      .getByTestId('chat-message-assistant')
      .count();
    await page.locator('textarea').fill(
      'Pesquise na internet informacoes atualizadas em 2026 sobre orientacoes oficiais da Receita Federal para a reforma tributaria do consumo e mostre somente paginas oficiais consultadas agora.'
    );
    await page.getByRole('button', { name: /enviar/i }).click();
    await expect(page.getByTestId('chat-message-assistant')).toHaveCount(
      currentCount + 1,
      { timeout: 180000 }
    );
    const currentAnswer = page.getByTestId('chat-message-assistant').last();
    await expect(currentAnswer).toContainText(
      /Atualizacoes oficiais recuperadas em tempo real/i
    );
    await expect(page.locator('body')).toContainText(
      /Fontes oficiais consultadas agora/i
    );
    await expect(page.locator('body')).toContainText(
      /Internet oficial: consultada/i
    );
    await currentAnswer.locator('details').last().locator('summary').click();
    await expect(
      currentAnswer.locator('a[href*="gov.br"]').last()
    ).toBeVisible();
    await page.screenshot({
      path: '../relatorios_melhorias/simulacoes/homologacao-usuario-ativo-final.png',
      fullPage: true,
    });
  });
});
