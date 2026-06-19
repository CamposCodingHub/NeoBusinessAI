# Melhorias Priorizadas

Data de consolidacao: 18 de junho de 2026

## Prioridade 1 - Estrategia e fundacao

### 1. Unificar marca, nome e narrativa

Problema:

- o repositorio mistura `NeoBusiness AI`, `LexScan` e `JurisFlow`.

Impacto:

- perda de clareza comercial;
- onboarding tecnico mais lento;
- documentacao inconsistente.

Acao:

- escolher a marca oficial;
- padronizar README, titulos, paginas e docs principais;
- definir uma frase curta de posicionamento.

### 2. Definir o objeto central do sistema

Problema:

- os modulos existem, mas ainda falta uma "materia/caso" como centro funcional do produto.

Acao:

- modelar relacoes claras entre cliente, caso, documento, prazo, peca, fatura e comunicacao;
- refletir isso no backend e no frontend.

## Prioridade 2 - Produto e experiencia

### 3. Tornar o dashboard realmente orientado a operacao

Acao:

- elevar o dashboard de pagina de atalhos para cockpit;
- exibir riscos, prazos criticos, cobranca atrasada, atividade do time e fila de IA;
- criar recomendacoes acionaveis.

### 4. Evoluir o modulo de documentos para um fluxo matter-based

Acao:

- permitir vincular upload a cliente/caso;
- gerar entidades e prazos automaticamente;
- salvar resumo, classificacao, risco e proxima acao.

### 5. Fortalecer o portal do cliente

Acao:

- permitir timeline de caso;
- documentos compartilhados;
- pagamento de faturas;
- atualizacoes automaticas;
- mensagens em um unico canal.

### 6. Tornar WhatsApp uma camada nativa de operacao

Acao:

- relacionar mensagens a cliente e caso;
- registrar historico;
- disparar automacoes por status de prazo/fatura;
- permitir templates aprovados por fluxo.

## Prioridade 3 - IA e automacao

### 7. Migrar de "resposta de IA" para "acao de IA"

Acao:

- deadline extraction -> criar tarefa;
- resumo documental -> atualizar caso;
- cobranca -> sugerir mensagem pronta;
- geracao de peca -> abrir rascunho versionado;
- relatorio -> consolidar insights automaticamente.

### 8. Especializar a IA por modulo

Trilhas sugeridas:

- documentos/processual;
- contratos/compliance;
- cobranca/negociacao;
- atendimento/cliente;
- pesquisa juridica.

### 9. Adicionar rastreabilidade e citacao de origem

Acao:

- toda sugestao de IA deve apontar documento, trecho, processo, evento ou dado de origem;
- registrar aprovacao humana nas acoes criticas.

## Prioridade 4 - Comercial e escala

### 10. Construir trilha forte de marketing e intake

Acao:

- captura de lead;
- triagem;
- agendamento;
- follow-up;
- scoring;
- conversao para cliente.

Benchmark associado:

- Lawmatics.

### 11. Estruturar planos por maturidade operacional

Sugestao:

- plano entrada: documentos + chat + prazos;
- plano crescimento: clientes + financeiro + portal;
- plano escritorio: time + cobranca + automacoes + WhatsApp;
- enterprise: compliance, integrações, multiunidade, auditoria forte.

## Prioridade 5 - Organizacao do repositorio

### 12. Tirar excesso de artefatos da raiz

Acao:

- mover analises para pasta dedicada;
- separar `docs/`, `reports/`, `strategy/`, `scripts/`;
- manter a raiz focada em codigo e bootstrap.

### 13. Definir o que e demo, beta e producao

Acao:

- marcar modulos simulados;
- marcar modulos prontos;
- listar dependencias externas obrigatorias;
- criar um checklist de readiness por modulo.

## Aposta recomendada

Se houver foco limitado, a melhor linha de evolucao e:

1. documentos;
2. prazos;
3. clientes;
4. cobranca;
5. WhatsApp;
6. portal do cliente;
7. IA de acao sobre esse fluxo.

Essa sequencia cria um produto mais defensavel do que tentar crescer em todas as direcoes ao mesmo tempo.
