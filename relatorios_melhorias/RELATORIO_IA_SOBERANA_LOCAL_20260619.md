# Relatorio da IA Soberana Local

Data: 19 de junho de 2026

## Resultado executivo

O NeoBusiness AI passou a operar com uma arquitetura de IA juridica local,
sem assinatura obrigatoria e sem dependencia operacional do Groq. A politica
ativa e `local_only`; a chave externa foi removida do ambiente local e os
clientes legados recusam inicializacao de provedores externos.

A consulta juridica rapida sobre tema curado foi reduzida de 709,4 segundos
na primeira integracao para 14,5 segundos no backend e 18,9 segundos na
jornada visual completa. A resposta final foi montada diretamente da base
normativa verificada, sem geracao livre, com fontes oficiais e locais
exibidas na interface.

## Computador utilizado

- CPU: Intel Xeon E5-2697A v4, 16 nucleos e 32 threads.
- Memoria: 31,84 GB.
- GPU: NVIDIA GeForce GT 710, 2 GB de VRAM.
- Inferencia: predominantemente CPU, com aproveitamento parcial da GPU nos
  modelos menores e embeddings.
- Custo de API na configuracao atual: zero.

## Oito frentes implementadas

1. Gateway unico de IA com roteamento local, auditoria, metricas, circuito de
   protecao e suporte a servidor local secundario.
2. Busca juridica hibrida lexical e semantica, com isolamento de documentos
   privados por usuario.
3. Corpus oficial local com Constituicao, codigos e leis brasileiras.
4. RAG juridico com citacoes, evidencias expansíveis e verificacao de artigos,
   paragrafos, fontes e associacoes normativas.
5. Avaliacao automatizada, benchmark de promocao e bloqueio de vazamento de
   prompt, jurisprudencia inventada e referencias nao recuperadas.
6. Pipeline governado de dataset para ajuste fino, com remocao de dados
   pessoais, revisao profissional e divisao deterministica de treino,
   validacao e teste.
7. Operacao resiliente com Ollama, Redis, PostgreSQL, Celery, watchdog,
   health checks, aquecimento de modelos e scripts idempotentes.
8. Experiencia integrada no produto, com status da IA, modelo, provedor,
   rota, latencia, tokens, confianca, fontes e auditorias visiveis.

## Rotas de inteligencia

- `quick_verified`: resposta deterministica para temas juridicos curados,
  produzida a partir da lei e das regras verificadas. Nao usa geracao livre.
- `quick_legal`: `lex-juridica-instant:1.5b` para perguntas curtas ainda nao
  cobertas pela camada curada.
- `balanced_legal`: `lex-juridica-rapida:3b` para analises interativas.
- `deep_legal`: `lex-juridica:14b` em fila assincrona para pesquisa profunda.
- `fast_general`: modelo auxiliar de 1,5B para tarefas gerais e classificacao.
- Embeddings: `nomic-embed-text`.

## Base juridica

- 10 fontes oficiais indexadas.
- 8.552 trechos pesquisaveis.
- 176 trechos com embeddings materializados; o restante e enriquecido de
  forma incremental conforme o uso.
- Priorizacao do artigo solicitado e dos dispositivos correlatos recuperados.
- Deduplicacao de citacoes e bloqueio de acesso cruzado a documentos privados.

## Controles de confiabilidade

- Fonte inexistente e removida antes da exibicao.
- Artigo nao recuperado e suprimido.
- Paragrafo associado ao artigo errado e suprimido.
- Conceitos juridicos curados associados ao artigo errado sao bloqueados.
- Alegacao de jurisprudencia sem decisao recuperada e removida.
- Tentativa de extrair prompt ou instrucao interna recebe resposta segura.
- Consultas juridicas permanecem marcadas para revisao do profissional
  responsavel.

## Validacoes executadas

- Suíte backend final: 170 testes aprovados.
- Cobertura final: 49,04%, acima da barreira configurada de 40%.
- Build Next.js de producao: aprovado, 29 rotas geradas.
- Teste visual final com cadastro, login, chat, fontes e auditoria: aprovado.
- Tempo visual final: 18,9 segundos.
- Tempo informado pelo backend na resposta final: 14,5 segundos.
- Benchmark soberano v3: 0,89055, aprovado, zero falhas criticas.
- Estado final: API, worker, frontend e Ollama com uma unica instancia cada.
- Groq: desabilitado pela politica local.

Artefatos principais:

- `simulacoes/ia-soberana-visual-final.png`
- `simulacoes/benchmark_ia_soberana_local_v3_20260619.json`
- `simulacoes/conversa_ia_soberana_validada_20260619.json`
- `logs/local_ai_watchdog.log`
- `logs_erros/playwright-results.json`

## Limites reais desta maquina

O sistema esta funcional, mas nao e tecnicamente correto chamar toda a IA de
instantanea neste hardware. Analises livres no modelo de 3B ainda podem levar
de aproximadamente dois a sete minutos, dependendo do tamanho do contexto,
aquecimento e quantidade de texto gerado. O modelo de 14B e adequado apenas
para tarefas assincronas e pode demorar muito.

O ajuste fino LoRA real nao foi executado: 2 GB de VRAM estao muito abaixo do
minimo seguro definido de 16 GB. O pipeline, os dados, a revisao e a exportacao
estao prontos, mas o treinamento deve aguardar hardware compativel. Nenhuma
alegacao de treinamento concluido foi feita.

## Proximas melhorias sem assinatura

- Ampliar continuamente as regras curadas para transformar mais perguntas
  frequentes em respostas verificadas de poucos segundos.
- Indexar novas fontes oficiais e manter historico de vigencia e versao.
- Criar mais benchmarks por area, especialmente penal, tributaria,
  trabalhista, consumidor, LGPD e contabil.
- Gerar exemplos de treinamento somente apos revisao de advogado ou contador.
- Usar um segundo computador local como endpoint redundante quando disponivel.

## Operacao

Iniciar a pilha:

```powershell
cd C:\Projetos\NeoBusinessAI\backend
powershell -ExecutionPolicy Bypass -File .\scripts\start_sovereign_stack.ps1 -Restart -WithWatchdog
```

Executar a barreira de qualidade:

```powershell
cd C:\Projetos\NeoBusinessAI\backend
powershell -ExecutionPolicy Bypass -File .\scripts\run_quality_gate.ps1
```

Executar a simulacao visual:

```powershell
cd C:\Projetos\NeoBusinessAI\frontend
npm run test:e2e:visual -- e2e/sovereign-local-ai.spec.ts
```
