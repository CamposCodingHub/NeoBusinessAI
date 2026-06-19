# Validacao da IA Juridica

Data: 18 de junho de 2026.

## Resultado final

### Backend

- Suite completa anterior: 123 testes aprovados.
- Suite focada final de IA, fontes e conversas: 28 testes aprovados.
- Build Python e importacao dos modulos: aprovados.
- Tres avisos externos de depreciacao do `httpx`, sem falha funcional.
- A configuracao global de cobertura ainda exige 70%, enquanto o repositorio mede 37,04%. Os testes passam com `--no-cov`; a cobertura e uma divida tecnica real.

### Frontend

- Build de producao Next.js: aprovado.
- Suite E2E consolidada: 13/13 testes aprovados.
- Testes visuais executados em navegador aberto e desacelerado.

### Testes visuais aprovados

- 10 testes de autenticacao, dashboard, documentos e simulador.
- Jornada critica completa: cadastro, onboarding, prazo, cliente, fatura, documento, chat e novo login.
- Pesquisa juridica CDC:
  - art. 26;
  - prazos de 30 e 90 dias;
  - evidencia oficial expansivel;
  - pergunta de seguimento sobre vicio oculto;
  - persistencia da conversa.
- Jornada longa:
  - upload de contrato real;
  - analise;
  - dez interacoes;
  - memoria do nome Operacao Atlas;
  - memoria do codigo NBLONG-2026;
  - mudanca para LGPD;
  - retorno ao caso;
  - e-mail executivo;
  - checklist;
  - persistencia apos navegacao.

## Evolucao do benchmark

### Benchmark inicial

- Respostas longas, mas erros de CDC e preventiva.
- Fontes sem citacao ligada a afirmacoes.
- Queda silenciosa para modelo 8B.
- Roteamento por substring.

### Benchmark intermediario

- 94/104 checagens.
- 7/7 consultas com fontes.
- 7/7 consultas com modelo robusto.
- Falhas de completude, omissao e referencias fora do recorte.

### Benchmark final gravado

Relatorio:

- `simulacoes/benchmark_ia_juridica_20260618_215413.json`
- `simulacoes/benchmark_ia_juridica_20260618_215413.md`

Resultado:

- 95/104 checagens;
- 4/8 cenarios com aprovacao integral;
- uma consulta recusada por limite externo, sem resposta inventada.

Depois desse relatorio, os quatro cenarios pendentes foram executados novamente:

- dolo eventual e culpa consciente: aprovacao integral;
- prisao preventiva: aprovacao integral;
- vicio e fato do produto: aprovacao integral;
- justa causa: aprovacao integral.

Essas quatro repeticoes nao foram agregadas ao JSON principal para preservar o historico do benchmark, mas foram registradas nos logs da sessao.

## Arquitetura validada

- Llama 3.3 70B como modelo juridico principal.
- GPT-OSS 120B como failover robusto.
- 8B somente para assistencia geral nao juridica.
- Falha segura se os dois modelos juridicos nao concluirem.
- Recuperacao de texto oficial do Planalto.
- Catalogo STF, STJ, TST, DataJud, ANPD e CARF.
- Guardrails curados para temas de alto risco.
- Auditoria automatica de artigos.
- Supressao de linhas com referencias nao recuperadas.
- Indicacao de modelo efetivo, fallback, completude e confianca.
- Continuidade de area juridica sem prender novos assuntos a area anterior.
- Evidencia normativa visivel na interface.

## Problemas encontrados e corrigidos

- `Leia` era confundido com `lei`.
- `clausula penal` acionava indevidamente o Codigo Penal.
- `execucao de contrato` podia superar LGPD no roteamento.
- Area antiga sobrepunha novo assunto explicito.
- Seguimento sobre vicio oculto caia no modelo geral.
- Humanizacao quebrava Markdown juridico.
- Respostas truncadas nao eram identificadas.
- Modelo alternativo 8B produzia erros legais.
- Frontend podia enviar pergunta antes de terminar a verificacao de status e cair no fallback sem chamar o backend.
- Fallback local gerava texto juridico generico; agora recusa com seguranca.

## Limitacoes e bloqueadores de producao

### Provedor de IA

O ambiente atual esta no tier on-demand:

- Llama 70B: limite observado de 100.000 tokens por dia.
- GPT-OSS 120B: limite observado de 8.000 tokens por minuto.

Os limites foram atingidos durante a bateria extensa. Para clientes reais:

- contratar Developer Tier ou capacidade equivalente;
- configurar alertas de quota e custo;
- adicionar outro provedor independente;
- manter fila distribuida por prioridade e plano;
- definir timeout, retry e circuit breaker.

### Infraestrutura

Logs atuais indicam:

- PostgreSQL configurado com erro de codificacao e fallback para SQLite;
- Redis indisponivel em alguns testes, com blacklist em modo degradado;
- SMTP nao configurado;
- Stripe nao configurado;
- Mercado Pago ainda depende de credenciais e validacao real;
- cobertura automatizada global abaixo da meta configurada.

Esses itens impedem afirmar que o sistema esta 100% pronto para producao, embora os fluxos funcionais locais estejam aprovados.

## Conclusao

A Lex deixou de ser um chat generico e passou a operar como um prototipo avancado de copiloto juridico verificavel. O comportamento mais importante validado foi: quando nao ha capacidade ou fundamento suficiente, a plataforma mostra fontes e se recusa a improvisar.

O proximo salto de qualidade depende menos de mudar o prompt e mais de:

- infraestrutura paga e redundante;
- pesquisa jurisprudencial com inteiro teor;
- benchmark revisado por advogados;
- base curada versionada;
- seguranca e multi-tenant auditados;
- cobertura de testes ampliada.
