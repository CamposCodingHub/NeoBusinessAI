# Estrategia da IA Juridica e Planos

Data de referencia: 18 de junho de 2026.

## Resumo executivo

O NeoBusiness AI deve ser posicionado como um sistema operacional para a advocacia brasileira com copiloto juridico verificavel. O diferencial nao deve ser "um chat que escreve muito", mas a combinacao de:

- pesquisa em fonte oficial;
- resposta com citacoes rastreaveis;
- separacao entre texto legal, interpretacao e estrategia;
- auditoria automatica de artigos;
- memoria do caso e dos documentos;
- execucao operacional de tarefas do escritorio;
- revisao humana obrigatoria em materia juridica;
- trilha de auditoria para saber qual fonte, modelo e versao produziram cada resposta.

Nao e tecnicamente ou eticamente correto prometer que uma IA "responde qualquer coisa sempre corretamente". O produto diferenciado promete outra coisa: buscar, fundamentar, mostrar lacunas, evitar invencoes, falhar de modo seguro e acelerar o trabalho do advogado sem ocultar incerteza.

## Diagnostico do motor anterior

O motor rapido de 8B era adequado para conversa geral, produtividade e resumos simples, mas insuficiente para pesquisa juridica profunda. Os primeiros benchmarks encontraram:

- respostas longas com erros objetivos no CDC;
- atribuicao incorreta de conteudo a artigos do CPP e da CLT;
- fontes apenas listadas no final, sem citacao ligada as afirmacoes;
- contaminacao do roteamento por substring, como "clausula penal" acionando o Codigo Penal;
- queda silenciosa para modelo menor quando o limite do provedor era atingido;
- historico longo consumindo o orcamento de tokens e aumentando falhas;
- formatacao aleatoria alterando estrutura juridica e Markdown.

Esses problemas nao podem ser resolvidos apenas pedindo ao modelo para "ser mais detalhado".

## Melhorias implementadas nesta etapa

- Roteador juridico por area e fonte oficial.
- Recuperacao direta de legislacao no Planalto.
- Fontes oficiais de STF, STJ e DataJud catalogadas.
- Selecao de artigos por assunto e por artigo solicitado.
- Modelo 70B para toda consulta juridica, inclusive consulta rapida.
- Modelo 8B reservado para assistencia geral nao juridica.
- Prompt juridico independente do prompt conversacional.
- Citacoes `[Fonte N]` e indice automatico de fontes.
- Auditoria de artigos citados contra os trechos recuperados.
- Evidencia normativa exibida na interface.
- Indicador de modelo solicitado, modelo efetivo e contingencia.
- Falha segura: se o modelo juridico nao concluir, nenhuma orientacao legal simulada e entregue.
- Fila local para reduzir estouro de limite do modelo maior.
- Benchmark factual com alegacoes proibidas e fatos obrigatorios.
- Teste visual preparado para CDC, evidencia oficial e continuidade.

## Diferencial recomendado

### 1. Resposta em duas camadas

Cada resultado deve exibir:

1. Evidencia verificada: texto oficial, artigo, URL, orgao, data de acesso e versao.
2. Analise da IA: interpretacao, aplicacao, riscos, fatos faltantes e estrategia.

O usuario nunca deve confundir uma inferencia da IA com o texto da lei.

### 2. Verificador adversarial

No modo profundo, um segundo agente deve tentar reprovar a resposta:

- conferir artigo e prazo;
- procurar contradicao entre resposta e fonte;
- detectar jurisprudencia inventada;
- identificar premissa factual nao fornecida;
- apontar tese contraria;
- gerar um placar de cobertura, nao uma falsa porcentagem de "verdade".

### 3. Pesquisa jurisprudencial real

A proxima camada deve integrar datasets e portais oficiais:

- STF e repercussao geral;
- STJ, repetitivos e sumulas;
- TST e jurisprudencia trabalhista;
- DataJud/CNJ para dados processuais;
- ANPD para guias e regulamentos;
- CARF para materia tributaria administrativa.

Um link para o portal nao equivale a recuperar o inteiro teor de um precedente. Ate a integracao existir, a IA deve dizer que a jurisprudencia nao foi recuperada.

### 4. Inteligencia por caso

Cada caso deve ter:

- fatos confirmados;
- fatos alegados;
- fatos controvertidos;
- cronologia;
- partes e papeis;
- pedidos;
- provas disponiveis e faltantes;
- teses favoraveis e contrarias;
- riscos;
- prazos;
- tarefas;
- documentos e versoes;
- conversas vinculadas ao caso.

### 5. Atualizacao temporal

Toda resposta juridica deve registrar:

- data da consulta;
- data de acesso da fonte;
- versao ou vigencia da norma;
- jurisdicao;
- tribunal;
- possibilidade de alteracao legislativa ou jurisprudencial.

### 6. Privacidade e governanca

Antes de vender para escritorios:

- criptografia em repouso e transito;
- segregacao real por tenant;
- controle de acesso por caso;
- log de acesso e exportacao;
- politica de retencao;
- mascaramento de CPF, segredo de justica e dados sensiveis;
- contrato com provedores impedindo treinamento com dados do cliente;
- plano de incidente;
- revisao LGPD;
- autenticacao multifator e SSO nos planos de equipe.

## Comparacao internacional

### Clio

O Clio combina gestao do escritorio, documentos, faturamento, portal, automacoes e IA. A pagina oficial informa planos a partir de US$49 por usuario e apresenta a IA como camada adicional orientada a resultados operacionais.

Aprendizado: nossa IA deve transformar analise em prazo, tarefa, documento, cobranca e comunicacao, nao terminar no texto do chat.

### Thomson Reuters CoCounsel

O CoCounsel se diferencia por pesquisa profunda, conteudo juridico autoritativo, redacao, revisao e integracao ao fluxo profissional.

Aprendizado: autoridade da fonte e rastreabilidade valem mais do que uma resposta eloquente.

### Lexis+ AI

O Lexis+ AI combina pesquisa, citacoes, drafting e conteudo proprietario.

Aprendizado: a vantagem defensavel e a base de conhecimento, o historico validado e a integracao, nao o modelo isolado.

### Jusbrasil e Jus IA

No Brasil, Jusbrasil e Jus IA ja educam o mercado para pesquisa, documentos e assistencia juridica por assinatura.

Aprendizado: o NeoBusiness deve evitar competir apenas em busca. A proposta precisa unir pesquisa verificavel, gestao do caso e operacao financeira/comercial.

## Estrategia de precos

### Explorar - R$0

- 10 consultas juridicas por mes;
- motor juridico de alta precisao;
- fontes oficiais e auditoria de artigos;
- 3 documentos;
- consulta rapida;
- sem pesquisa profunda e sem geracao completa de pecas.

Objetivo: demonstrar confianca e converter, sem oferecer uma experiencia juridica de qualidade inferior.

### Profissional - R$149/mes

- 150 consultas juridicas;
- 30 pesquisas profundas;
- 50 documentos;
- geracao e revisao de pecas;
- memoria de casos;
- prazos, clientes e financeiro;
- 1 usuario.

Justificativa: preco acessivel para autonomos, superior a ferramentas genericas de IA, mas abaixo do custo percebido de pesquisa e operacao separadas.

### Escritorio - R$699/mes

- 5 usuarios;
- 1.000 consultas;
- 300 pesquisas profundas;
- 500 documentos;
- base de conhecimento do escritorio;
- WhatsApp, cobranca e portal;
- aprovacao e auditoria;
- fila prioritaria.

Justificativa: R$139,80 por usuario com ganho de equipe e recursos operacionais. Deve haver politica de uso justo para evitar revenda ou automacao abusiva.

### Scale - a partir de R$1.990/mes

- 15 usuarios ou mais;
- franquia negociada;
- API e webhooks;
- SSO;
- ambientes segregados;
- politicas de retencao;
- SLA;
- implantacao e workflows customizados.

Recomendacao comercial: cobrar onboarding entre R$2.500 e R$15.000 conforme migracao, integracoes e treinamento. Grandes volumes de IA, armazenamento e suporte devem ser precificados separadamente.

## Economia unitaria da IA

Na pagina oficial consultada em 18 de junho de 2026, o Llama 3.3 70B Versatile custa:

- US$0,59 por 1 milhao de tokens de entrada;
- US$0,79 por 1 milhao de tokens de saida.

Uma consulta com 3.000 tokens de entrada e 1.000 de saida custa aproximadamente US$0,00256 apenas em inferencia. O custo real do produto inclui recuperacao, banco, OCR, armazenamento, observabilidade, suporte, pagamentos, seguranca, desenvolvimento e fontes licenciadas.

O ambiente atual usa limite gratuito/on-demand de 100.000 tokens por dia no 70B, que foi atingido durante os testes. Producao exige Developer Tier ou equivalente, multiplos provedores e monitoramento de custo/limite.

## O que nao deve variar por plano

- proibicao de inventar precedente;
- uso de fonte oficial quando disponivel;
- auditoria de artigo;
- aviso de incerteza;
- protecao de dados;
- falha segura;
- necessidade de revisao profissional.

Planos podem variar volume, tamanho do contexto, profundidade, prioridade, automacoes, numero de usuarios, armazenamento, integracoes e SLA.

## Roadmap prioritario

### P0 - antes de clientes reais

- conta paga e limites de producao do provedor;
- segundo provedor de IA com failover;
- benchmark revisado por advogados;
- monitoramento por area do Direito;
- politica de privacidade e termos especificos para IA juridica;
- MFA;
- backup testado;
- isolamento multi-tenant auditado;
- remocao de credenciais e dados de teste;
- alertas de custo e indisponibilidade.

### P1 - diferenciacao

- pesquisa real STF/STJ/TST;
- verificador adversarial;
- citacao por trecho;
- workspace por caso;
- cronologia e mapa de provas;
- geracao de peca com matriz fato-fonte-tese;
- comparacao de versoes de documentos;
- ingestao de pastas e emails;
- aprovacao humana antes de enviar ou protocolar.

### P2 - escala

- filas distribuidas;
- cache por fonte e artigo;
- indice vetorial por tenant;
- workers de OCR;
- telemetria de tokens e custo por cliente;
- limites por plano;
- billing real e webhooks idempotentes;
- SLA e painel de status;
- avaliacao continua com regressao juridica.

## Criterio de excelencia

Antes de divulgar a Lex como referencia da categoria, a meta recomendada e:

- pelo menos 1.000 perguntas de benchmark;
- cobertura penal, civil, processual, consumidor, trabalhista, tributaria, empresarial, constitucional, administrativo e LGPD;
- revisao independente por advogados;
- zero precedentes inventados nos testes de liberacao;
- 100% das afirmacoes normativas centrais com fonte;
- respostas que se recusam quando a base nao e suficiente;
- testes de prompt injection em documentos;
- testes de segredo de justica e dados pessoais;
- registro publico das limitacoes conhecidas.

## Fontes consultadas

- https://www.clio.com/pricing/
- https://legal.thomsonreuters.com/en/products/cocounsel-legal
- https://www.thomsonreuters.com/en/cocounsel
- https://store.lexisnexis.com/lawfirms
- https://www.lexisnexis.com/en-int/products/lexis-plus-ai
- https://www.jusbrasil.com.br/pro
- https://ia.jusbrasil.com.br/planos
- https://console.groq.com/docs/model/llama-3.3-70b-versatile
- https://console.groq.com/docs/models
- https://console.groq.com/docs/rate-limits
- https://groq.com/pricing
- https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm
- https://portal.stf.jus.br/jurisprudencia/
- https://transparencia.stj.jus.br/tecnologia-da-informacao-e-comunicacao/dados-abertos/
- https://datajud-wiki.cnj.jus.br/api-publica/
- https://www.gov.br/anpd/pt-br
- https://carf.economia.gov.br/jurisprudencia/acordaos-carf-2
