import { expect, test } from '@playwright/test';
import { authenticatePage } from './helpers';

const contractText = `
CONTRATO DE PRESTACAO DE SERVICOS - OPERACAO ATLAS

Codigo interno do contrato: NBLONG-2026.
Contratante: Atlas Comercio Digital Ltda.
Contratada: Horizonte Tecnologia Juridica Ltda.
Valor mensal: R$ 18.750,00.
Vigencia: 24 meses a partir de 18 de junho de 2026.
Reajuste: IPCA a cada 12 meses.
Rescisao imotivada: aviso previo minimo de 60 dias.
Multa por rescisao antecipada: tres mensalidades.
Prazo para notificacao de incidente de seguranca: 24 horas.
Prazo para corrigir inadimplemento: 15 dias.
Foro: Comarca de Sao Paulo, Estado de Sao Paulo.

Obrigacoes relevantes:
- A contratada deve manter confidencialidade por cinco anos.
- Dados pessoais devem ser tratados conforme a LGPD.
- Subcontratacao depende de autorizacao escrita.
- Relatorios mensais devem ser entregues ate o quinto dia util.

Risco declarado pelas partes:
O anexo de nivel de servico ainda nao define disponibilidade minima nem
penalidade por indisponibilidade.
`.trim();

test('jornada longa: arquivo real, analise, dez conversas e persistencia', async ({
  page,
  request,
}) => {
  test.setTimeout(1200000);

  await authenticatePage(page, request);
  const documentName = `operacao-atlas-${Date.now()}.txt`;

  await test.step('upload e analise real do contrato', async () => {
    await page.goto('/dashboard/documents');
    await page.locator('#file-input').setInputFiles({
      name: documentName,
      mimeType: 'text/plain',
      buffer: Buffer.from(contractText, 'utf-8'),
    });
    await page.getByRole('button', { name: /fazer upload/i }).click();
    await expect(page.getByText(documentName)).toBeVisible({ timeout: 30000 });

    await page.getByRole('button', { name: /analisar/i }).first().click();
    await expect(
      page.getByText('Analise concluida e documento atualizado.')
    ).toBeVisible({ timeout: 120000 });
  });

  await test.step('conectar documento ao chat', async () => {
    await page.goto('/chat');
    await page
      .getByRole('listbox', { name: /documento em contexto/i })
      .selectOption({ label: documentName });
    await expect(page.getByTestId('document-context-status')).toContainText(
      'Contexto analisado conectado',
      { timeout: 30000 }
    );
  });

  const prompts = [
    'Resuma o documento selecionado sem inventar informacoes.',
    'Liste as partes identificadas no arquivo selecionado.',
    'Quais valores foram extraidos do documento?',
    'Quais prazos foram extraidos do arquivo?',
    'Liste os riscos registrados na analise do documento.',
    'Faca uma sintese das evidencias do arquivo em topicos.',
    'Compare o resumo e a analise persistida do documento.',
    'Liste somente evidencias verificaveis do arquivo.',
    'Consolide partes, prazos, valores e riscos do documento.',
    'Feche com um checklist das evidencias do arquivo para revisao humana.',
  ];

  await test.step('executar conversa prolongada com dez interacoes', async () => {
    await page.getByRole('button', { name: /consulta rapida/i }).click();

    for (const prompt of prompts) {
      const assistantCount = await page
        .getByTestId('chat-message-assistant')
        .count();
      await page.locator('textarea').fill(prompt);
      await page.getByRole('button', { name: /enviar/i }).click();
      await expect(page.getByTestId('chat-message-assistant')).toHaveCount(
        assistantCount + 1,
        { timeout: 180000 }
      );
    }

    await expect(page.locator('body')).toContainText(
      /Evidencias dos documentos selecionados/i
    );
    await expect(page.locator('body')).toContainText(documentName);
    await expect(page.getByTestId('chat-message-user')).toHaveCount(10);
  });

  await test.step('sair e retornar sem perder a tarefa longa', async () => {
    await page.goto('/dashboard');
    await page.goto('/chat');

    await expect(page.getByTestId('chat-message-user')).toHaveCount(10);
    await expect(page.locator('body')).toContainText(
      'Feche com um checklist das evidencias'
    );
  });
});
