# Relatorio de escalabilidade, documentos e IA profissional

Data: 19 de junho de 2026

## Resultado executivo

O ciclo endureceu o fluxo de documentos, ampliou a IA para rotinas contabeis e
fiscais, criou contingencia profissional para indisponibilidade do LLM e validou
o produto em testes unitarios, integrados, de carga e visuais.

Estado final:

- API, PostgreSQL, Redis, Celery e frontend operacionais.
- Health geral `degraded` de forma intencional porque a geracao Groq esta em 429,
  embora o endpoint de modelos esteja acessivel.
- 149/149 testes backend aprovados.
- Cobertura total ativa: 44,71%, acima do gate de 40%.
- 16/16 jornadas Playwright aprovadas em navegador visivel.
- 8/8 cenarios extremos de documentos aprovados.
- Build de producao Next.js aprovado.
- Nenhum novo HTTP 500, traceback ou erro fatal nos logs finais.

## Documentos e seguranca

O upload principal deixou de carregar arquivos inteiros em memoria. Agora:

- grava em blocos de 1 MB;
- interrompe ao ultrapassar 50 MB;
- calcula SHA-256 durante o envio;
- valida extensao, assinatura real e MIME;
- valida a estrutura interna de DOCX;
- bloqueia executaveis disfarçados e extensoes duplas perigosas;
- remove DOC legado da oferta e aceita DOCX, PDF, TXT, RTF, JPG, PNG e TIFF;
- limita PDF digital a 500 paginas e OCR a 100 paginas;
- limita imagem a 40 milhoes de pixels;
- limita texto extraido a 2 milhoes de caracteres;
- preserva inicio e fim em arquivos de texto extensos;
- registra metodo, truncamento, paginas, hash, MIME e modo de analise.

Arquivos gerados e simulados:

- TXT de 12.582.620 bytes;
- TXT de 53.477.376 bytes, rejeitado com HTTP 413;
- PDF de 250 paginas, analisado;
- PDF de 501 paginas, rejeitado na analise com HTTP 422;
- DOCX com 9.000 paragrafos;
- RTF de aproximadamente 5 MB;
- PDF executavel disfarçado, rejeitado com HTTP 400;
- manual publico IRPF 2026 da Receita, com 340 paginas e 4.751.936 bytes.

Relatorio detalhado:

- `relatorios_melhorias/simulacoes/estresse_documentos_20260619_073839.md`

## IA juridico-contabil

Foram incorporadas fontes oficiais e roteamento especializado para:

- DCTFWeb e MIT;
- eSocial;
- Normas Brasileiras de Contabilidade;
- obrigatoriedade de escrituracao contabil;
- IRPF 2026;
- IBS e CBS na reforma tributaria de 2026;
- Domicilio Judicial Eletronico;
- legislacao federal ja coberta pelo produto.

A IA agora identifica dominios `juridico`, `contabil_fiscal` e
`juridico_contabil`, indica o profissional revisor e evita inventar aliquota,
prazo, leiaute, obrigacao, artigo ou precedente.

Quando o modelo robusto esta indisponivel, a resposta nao fica mais curta. A
contingencia:

- recupera e apresenta evidencias oficiais;
- aplica regras factuais curadas;
- preserva fatos centrais da conversa;
- produz checklist de validacao;
- monta matriz RACI quando solicitada;
- diferencia advogado, contador, RH e diretoria;
- informa claramente que o LLM nao gerou conclusao individualizada.

O benchmark final aprovou 107/127 checagens. As 20 checagens restantes sao
exatamente duas por caso: modelo robusto indisponivel e modelo degradado. Todas
as verificacoes de detalhamento, fontes, dominio, termos, revisao humana,
memoria e ausencia de referencias nao verificadas passaram.

Relatorio detalhado:

- `relatorios_melhorias/simulacoes/benchmark_ia_profissional_20260619_082026.md`

## Fontes oficiais pesquisadas

- Receita Federal, IRPF 2026:
  https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/perguntas-e-respostas/dirpf/p-r-irpf-2026-v1-00-2026-04-23.pdf
- Receita Federal, DCTFWeb:
  https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/DCTFWeb
- eSocial, perguntas frequentes:
  https://www.gov.br/esocial/pt-br/empresas/perguntas-frequentes
- CFC, Normas Brasileiras de Contabilidade:
  https://cfc.org.br/tecnica/normas-brasileiras-de-contabilidade/
- CFC, obrigatoriedade de escrituracao:
  https://cfc.org.br/tecnica/perguntas-frequentes/obrigatoriedade-de-escrituracao-contabil/
- Receita Federal, reforma tributaria em 2026:
  https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-tributaria-do-consumo/orientacoes-2026
- CNJ, Domicilio Judicial Eletronico:
  https://www.cnj.jus.br/tecnologia-da-informacao-e-comunicacao/justica-4-0/domicilio-judicial-eletronico/perguntas-frequentes/

## Risco residual e recomendacao

O risco operacional principal e a cota gratuita do Groq. Durante o benchmark,
o provedor retornou HTTP 429 depois do estresse de documentos. A contingencia
local manteve o produto util, detalhado, fundamentado e transparente, mas nao
substitui integralmente um modelo robusto.

Para operacao comercial continua:

1. contratar capacidade paga com SLA;
2. configurar um segundo provedor robusto;
3. manter a contingencia atual como terceira camada;
4. monitorar consumo, 429, latencia, custo por consulta e taxa de fallback;
5. o health check ja foi corrigido para marcar o provedor e o sistema como
   `degraded` quando a geracao falha recentemente, mesmo que `/models` responda.
