"""Seed de exemplos profissionais Lex (CLT, CPC, CTN, NBC, societario, escritorio).

Nao inventa dispositivos: outputs idealizam grounding via retrieval e disclaimers.
Idempotente via content_hash do TrainingDatasetService.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

SEED_VERSION = "professional_lex_1.1.0"
SOURCE_TYPE = "curated_seed_professional"

# ~25 exemplos de alta qualidade; estilo: conciso, estruturado, sem emoji.
EXAMPLES: list[dict[str, Any]] = [
    # --- Trabalhista / CLT ---
    {
        "domain": "trabalhista",
        "instruction": (
            "Qual a jornada padrao e como tratar horas extras na CLT?"
        ),
        "input_text": (
            "[Fonte 1] CLT recuperada: jornada ordinaria de ate 8 horas diarias "
            "e 44 semanais, salvo excecoes legais ou convencionais; trabalho "
            "extraordinario sujeito a acrescimo minimo previsto na norma "
            "recuperada. CCT do sindicato nao anexada."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "A jornada ordinaria padrao, no trecho recuperado, e de ate 8h/dia "
            "e 44h/semana, com extraordinario sujeito ao acrescimo minimo da "
            "norma [Fonte 1]. Excecoes e regimes especiais exigem checagem da "
            "CLT integral e da CCT aplicavel.\n\n"
            "## Aplicacao\n"
            "Confirme cargo, escala real, banco de horas, acordo individual/"
            "coletivo e recibos antes de calcular valores. Sem CCT e cartoes de "
            "ponto, qualquer estimativa numerica e provisoria.\n\n"
            "## Limite\n"
            "Nao invente percentual de adicional nem artigo alem do trecho "
            "recuperado. Revise com o advogado trabalhista responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "trabalhista",
        "instruction": (
            "Monte o checklist de rescisao sem inventar verbas finais."
        ),
        "input_text": (
            "[Fonte 1] CLT: verbas tipicas em terminacao do contrato incluem "
            "saldos de salario, aviso, ferias e 13 proporcional conforme "
            "modalidade de ruptura; valores dependem de fatos e documentos. "
            "Nao ha CCT nem extratos no contexto."
        ),
        "output_text": (
            "## Checklist (sem numeros finais)\n"
            "1. Modalidade de saida (pedido, dispensa com/sem justa causa, "
            "acordo) e datas de admissao/saida.\n"
            "2. Documentos: CTPS, contrato, cartoes, recibos, TRCT, guia FGTS/"
            "seguro-desemprego quando cabivel.\n"
            "3. Confrontar cada rubrica com o trecho CLT recuperado [Fonte 1] "
            "e com a CCT — nao inventar aliquotas ou percentuais.\n"
            "4. Homologacao/assistencia sindical apenas se a norma vigente "
            "exigir no caso concreto.\n\n"
            "## Limite\n"
            "Sem base documental, nao feche valor liquido. Revise com o "
            "advogado responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "trabalhista",
        "instruction": (
            "Cite o artigo da CLT sobre intervalo intrajornada. Nada foi "
            "recuperado."
        ),
        "input_text": (
            "Nenhum artigo da CLT foi recuperado nesta execucao."
        ),
        "output_text": (
            "Nao e seguro citar numero de artigo sobre intervalo intrajornada "
            "sem o texto da CLT recuperado nesta execucao. Proximo passo: "
            "recuperar o dispositivo vigente no Planalto/base oficial e, se "
            "houver CCT, confrontar a regra coletiva. Ate la, limite-se a "
            "indicar a necessidade de grounding e revisao profissional."
        ),
        "citations": [],
    },
    {
        "domain": "trabalhista",
        "instruction": (
            "O empregado alega jornada 12x36. Posso confirmar legalidade?"
        ),
        "input_text": (
            "[Fonte 1] Trecho CLT sobre escalas especiais menciona possibilidade "
            "de regimes diferenciados quando autorizados por lei ou negociacao "
            "coletiva, com requisitos proprios. Faltam escala assinada e CCT."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "Nao confirme legalidade automatica da escala 12x36 sem documentos. "
            "O trecho recuperado indica regimes diferenciados condicionados a "
            "autorizacao legal ou negociacao coletiva [Fonte 1].\n\n"
            "## Fatos faltantes\n"
            "Escala escrita, CCT/ACT, cargo, compensacoes e registros de "
            "ponto. Com esses elementos, reavalie o enquadramento.\n\n"
            "Revisao do advogado trabalhista e obrigatoria antes de orientar "
            "o cliente."
        ),
        "citations": ["Fonte 1"],
    },
    # --- Civel / CPC ---
    {
        "domain": "civel_cpc",
        "instruction": (
            "Explique tutela de urgencia no CPC com base no trecho."
        ),
        "input_text": (
            "[Fonte 1] CPC recuperado: tutela de urgencia exige probabilidade "
            "do direito e perigo de dano ou risco ao resultado util do "
            "processo; decisao deve ser fundamentada."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "A tutela de urgencia, no trecho recuperado, exige probabilidade "
            "do direito e perigo de dano (ou risco ao resultado util), com "
            "decisao fundamentada [Fonte 1].\n\n"
            "## Aplicacao\n"
            "Estruture o pedido com fatos, provas e urgencia concreta. Sem "
            "documentos, a probabilidade do direito permanece hipotetica.\n\n"
            "## Limite\n"
            "Nao invente artigo alem do recuperado. Revise a peca com o "
            "advogado responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "civel_cpc",
        "instruction": (
            "Qual o prazo de contestacao? So tenho a mencao generica do cliente."
        ),
        "input_text": (
            "Cliente diz que foi citado. Nenhum trecho do CPC sobre prazo de "
            "contestacao foi recuperado; nao ha copia da citacao."
        ),
        "output_text": (
            "Nao e possivel afirmar o prazo de contestacao sem o texto do CPC "
            "recuperado e sem a peca de citacao (modalidade, data de ciencia, "
            "autos digitais). Solicite a citacao/intimacao, confirme a "
            "contagem no sistema do tribunal e so entao calcule o termo. "
            "Qualquer dia inventado cria risco processual. Revisao do "
            "advogado responsavel e indispensavel."
        ),
        "citations": [],
    },
    {
        "domain": "civel_cpc",
        "instruction": (
            "Analise risco de contrato de prestacao de servicos com fatos "
            "incompletos."
        ),
        "input_text": (
            "[Base Local 1] Cliente alega inadimplemento da contraparte, mas "
            "nao anexou contrato, aditivos, e-mails nem comprovantes de "
            "pagamento."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "Sem o instrumento e as provas de cumprimento, nao conclua mora, "
            "multa ou rescisao [Base Local 1].\n\n"
            "## Proximos passos\n"
            "Peca contrato integral, aditivos, notificacoes, comprovantes e "
            "cronologia. Separe merito (obrigacoes) de estrategia processual "
            "(CPC) so apos o acervo minimo.\n\n"
            "Resposta provisoria; revisao do advogado responsavel."
        ),
        "citations": ["Base Local 1"],
    },
    {
        "domain": "civel_cpc",
        "instruction": (
            "Estruture analise de peticao inicial sem inventar requisitos "
            "fora do CPC recuperado."
        ),
        "input_text": (
            "[Fonte 1] CPC: peticao inicial deve indicar partes, fato e "
            "fundamentos, pedido com suas especificacoes e valor da causa, "
            "entre outros requisitos do trecho recuperado."
        ),
        "output_text": (
            "## Checklist ancorado\n"
            "- Partes e qualificacao\n"
            "- Fatos e fundamentos juridicos\n"
            "- Pedidos determinados e valor da causa\n"
            "- Demais requisitos expressos em [Fonte 1]\n\n"
            "Nao acrescente requisitos de memoria do modelo. Se faltar trecho "
            "sobre documento indispensavel ou emenda, diga que nao foi "
            "recuperado. Revisao do advogado responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    # --- Tributario / CTN ---
    {
        "domain": "tributario",
        "instruction": (
            "O que e lancamento e constituicao do credito tributario no CTN?"
        ),
        "input_text": (
            "[Fonte 1] CTN recuperado: lancamento e procedimento "
            "administrativo que verifica a ocorrencia do fato gerador, "
            "determina a materia tributavel, calcula o montante e identifica "
            "o sujeito passivo, constituindo o credito tributario."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "No trecho recuperado, o lancamento constitui o credito "
            "tributario ao verificar o fato gerador, delimitar a materia "
            "tributavel, calcular o montante e identificar o sujeito passivo "
            "[Fonte 1].\n\n"
            "## Aplicacao\n"
            "Confirme modalidade (de oficio, por homologacao etc.) apenas se "
            "o texto recuperado ou o auto/notificacao a indicar. Sem esses "
            "elementos, nao classifique o caso.\n\n"
            "Nao informe aliquota. Revisao do contador/advogado tributarista."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "tributario",
        "instruction": (
            "Qual a aliquota de ISS para meu cliente de TI em Sao Paulo?"
        ),
        "input_text": (
            "Nenhuma lei municipal, lista de servicos ou tabela vigente foi "
            "recuperada."
        ),
        "output_text": (
            "Nao posso informar aliquota de ISS sem a norma municipal vigente "
            "e o enquadramento do servico recuperados nesta execucao. "
            "Inventar percentual e incorreto e arriscado. Consulte a "
            "legislacao do municipio competente e a lista de servicos "
            "aplicavel ao fato gerador, com revisao do contador responsavel."
        ),
        "citations": [],
    },
    {
        "domain": "tributario",
        "instruction": (
            "Explique credito tributario e suspensao sem inventar prazos de "
            "pagamento."
        ),
        "input_text": (
            "[Fonte 1] CTN: credito tributario regularmente constituido tem "
            "exigibilidade que pode ser suspensa nas hipoteses legais "
            "previstas no trecho (ex.: deposito, reclamacoes/recursos nos "
            "termos da norma). Prazos especificos de vencimento nao constam."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "O credito constituido segue o regime do CTN recuperado; a "
            "exigibilidade pode ser suspensa nas hipoteses do trecho "
            "[Fonte 1].\n\n"
            "## Limite\n"
            "Prazos de vencimento, parcelamento ou multa nao foram "
            "recuperados — nao invente dias nem percentuais. Peça o "
            "auto/notificacao e a norma regulamentar do tributo concreto.\n\n"
            "Revisao profissional obrigatoria."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "tributario",
        "instruction": (
            "Posso orientar compensacao tributaria so com o relato verbal?"
        ),
        "input_text": (
            "Cliente alega credito de PIS/COFINS. Nenhum PER/DCOMP, escritura "
            "fiscal ou norma especifica foi recuperada."
        ),
        "output_text": (
            "Nao. Compensacao exige base documental e enquadramento normativo "
            "verificado. Sem escritura, demonstrativos e norma recuperada, "
            "qualquer orientacao de compensar e especulativa e pode gerar "
            "auto de infracao. Solicite os documentos e recupere a regra "
            "vigente antes de recomendar ato. Revisao do contador/tributarista."
        ),
        "citations": [],
    },
    # --- Contabil / NBC ---
    {
        "domain": "contabil_nbc",
        "instruction": (
            "O que a NBC espera de escrituracao regular?"
        ),
        "input_text": (
            "[Fonte 1] Orientacao CFC/NBC recuperada: a escrituracao deve ser "
            "completa, em idioma e moeda nacionais, com base em documentacao "
            "habil e em ordem cronologica, observando o framework vigente "
            "citado no trecho. Detalhes de leiaute ECD nao constam."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "No trecho CFC/NBC recuperado, a escrituracao deve ser completa, "
            "cronologica, em moeda/idioma nacionais e lastreada em "
            "documentacao habil [Fonte 1].\n\n"
            "## Limite\n"
            "Nao invente codigo de conta, leiaute ECD ou numero de NBC alem "
            "do recuperado. Confirme o framework vigente no CFC e a "
            "politica contabil da entidade com o contador CRC responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "contabil_nbc",
        "instruction": (
            "Quais demonstracoes contabeis apresentar? Cite NBC inventada se "
            "preciso."
        ),
        "input_text": (
            "[Fonte 1] Trecho NBC: conjunto completo tipicamente inclui "
            "balanco patrimonial, demonstracao do resultado, demonstracoes "
            "de mutacoes do patrimonio liquido e dos fluxos de caixa, e "
            "notas explicativas, conforme aplicabilidade ao tipo de entidade. "
            "Excecoes para PME nao detalhadas aqui."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "Segundo o trecho recuperado, o conjunto tipico inclui BP, DRE, "
            "DMPL, DFC e notas, conforme aplicabilidade [Fonte 1].\n\n"
            "## Limite\n"
            "Nao cito NBC com numero inventado. Se o cliente for PME ou "
            "regime simplificado, recupere a norma especifica antes de "
            "excluir demonstracoes. Revisao do contador responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "contabil_nbc",
        "instruction": (
            "Qual o codigo exato da NBC TG sobre reconhecimento de receita?"
        ),
        "input_text": (
            "Nenhuma NBC sobre receita foi recuperada nesta execucao."
        ),
        "output_text": (
            "Nao informo codigo de NBC sem o texto oficial recuperado. "
            "Inventar numeracao viola a regra de grounding. Consulte o "
            "portal do CFC pelas NBCs vigentes sobre receita e confirme a "
            "versao aplicavel ao exercicio. Revisao do contador CRC."
        ),
        "citations": [],
    },
    {
        "domain": "contabil_nbc",
        "instruction": (
            "Cliente quer mudar politica contabil no meio do exercicio. Como "
            "responder?"
        ),
        "input_text": (
            "[Fonte 1] Trecho NBC: mudanca de estimativa e mudanca de politica "
            "possuem tratamentos distintos; politica geralmente com efeito "
            "retrospectivo quando exigido pela norma, sujeito a "
            "impraticabilidade e divulgacao em notas."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "Separe mudanca de estimativa de mudanca de politica. O trecho "
            "indica tratamento distinto e, para politica, efeito "
            "retrospectivo quando a norma exigir, com divulgacao [Fonte 1].\n\n"
            "## Fatos faltantes\n"
            "Motivo da mudanca, demonstracoes afetadas, impraticabilidade e "
            "impacto fiscal. Nao aprove a mudanca sem essa analise.\n\n"
            "Revisao do contador responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    # --- Societario ---
    {
        "domain": "societario",
        "instruction": (
            "Quorum de deliberacao em LTDA: posso inventar percentual?"
        ),
        "input_text": (
            "[Fonte 1] Lei recuperada trata de deliberacoes de socios em "
            "sociedade limitada conforme quoruns legais e o contrato social. "
            "O contrato social desta empresa nao foi anexado."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "Quoruns dependem da materia, da lei aplicavel recuperada e do "
            "contrato social [Fonte 1]. Sem o contrato, nao invente "
            "percentual.\n\n"
            "## Proximo passo\n"
            "Obtenha contrato social/aditivos e a ata pretendida; confronte "
            "com o trecho legal recuperado. Revisao do advogado societario."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "societario",
        "instruction": (
            "Cliente quer transformar LTDA em S.A. Resuma cuidados."
        ),
        "input_text": (
            "[Fonte 1] Normas recuperadas distinguem regimes de sociedade "
            "limitada e anonima (governanca, capital, publicidade de atos). "
            "Nao ha projeto de estatuto no contexto."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "A transformacao troca o regime de governanca e publicidade; o "
            "trecho recupera a distincao entre LTDA e S.A. [Fonte 1], mas "
            "sem estatuto e mapa de capital nao ha como validar passos.\n\n"
            "## Checklist\n"
            "Contrato atual, capital, socios, orgaos, registro na Junta/"
            "CVM se cabivel, e impactos fiscais/contabeis com o contador.\n\n"
            "Nao misture regras dos dois tipos. Revisao profissional."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "societario",
        "instruction": (
            "Socio minoritario pede acesso a livros. Como estruturar?"
        ),
        "input_text": (
            "[Fonte 1] Trecho legal/contratual generico: socios podem ter "
            "direitos de informacao e fiscalizacao nos limites da lei e do "
            "contrato. Contrato social nao anexado."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "O direito de informacao existe nos limites da lei e do contrato "
            "[Fonte 1], mas o alcance concreto depende do instrumento "
            "societario e do tipo de livro pedido.\n\n"
            "## Fatos faltantes\n"
            "Contrato/estatuto, percentual de participacao, livros "
            "solicitados e eventual litigio. Evite prometer acesso irrestrito "
            "sem base. Revisao do advogado societario."
        ),
        "citations": ["Fonte 1"],
    },
    # --- Escritorio / ops ---
    {
        "domain": "escritorio_ops",
        "instruction": (
            "Como gerir prazo fatal sem inventar dias de contagem?"
        ),
        "input_text": (
            "[Base Local 1] Intimacao juntada hoje no PJe; tipo de ato ainda "
            "nao classificado pela equipe. CPC sobre o prazo especifico nao "
            "recuperado."
        ),
        "output_text": (
            "## Protocolo\n"
            "1. Identificar o ato intimado e a data/hora de ciencia no "
            "tribunal [Base Local 1].\n"
            "2. Recuperar a regra de prazo no CPC/lei especial aplicavel — "
            "nao inventar dias.\n"
            "3. Registrar no sistema interno com alerta e responsavel.\n"
            "4. Confirmar feriados locais e suspensoes oficiais.\n\n"
            "Ate concluir esses passos, trate o prazo como nao calculado. "
            "Revisao do advogado responsavel."
        ),
        "citations": ["Base Local 1"],
    },
    {
        "domain": "escritorio_ops",
        "instruction": (
            "Novo lead: parte adversa ja e cliente em outra area. Como "
            "tratar COI?"
        ),
        "input_text": (
            "[Base Local 1] Cadastro interno indica cliente ativo com a parte "
            "que agora figura no polo contrario do lead."
        ),
        "output_text": (
            "## Conflito potencial\n"
            "Ha indicio de conflito de interesses: a parte adversa do lead ja "
            "e cliente ativo [Base Local 1].\n\n"
            "## Acao\n"
            "Nao aceite o mandato nem compartilhe informacoes privilegiadas. "
            "Acione o screening interno/COI, avalie consentimento informado "
            "somente se eticamente cabivel e documente a decisao. Em duvida, "
            "recuse. Revisao da lideranca do escritorio."
        ),
        "citations": ["Base Local 1"],
    },
    {
        "domain": "escritorio_ops",
        "instruction": (
            "Proponha honorarios para causa trabalhista sem tabela inventada."
        ),
        "input_text": (
            "Cliente pergunta valor. Nenhuma tabela da OAB local nem proposta "
            "escrita foi anexada."
        ),
        "output_text": (
            "## Estrutura (sem numeros inventados)\n"
            "Discuta formato: fixo, por fase, exito e/ou hora; escopo; "
            "custas; e criterios de reajuste. Remeta a tabela da seccional "
            "da OAB e ao acordo escrito (contrato de honorarios).\n\n"
            "Nao invente percentuais ou valores de tabela. Documente a "
            "proposta apos alinhamento comercial e revisao do responsavel."
        ),
        "citations": [],
    },
    {
        "domain": "escritorio_ops",
        "instruction": (
            "Cliente pede para ignorar COI e 'so dar um parecer rapido'."
        ),
        "input_text": (
            "[Base Local 1] Mesmo grupo economico ja atendido pelo escritorio "
            "em mandato confidencial correlato."
        ),
        "output_text": (
            "Nao. Parecer informal nao elimina conflito quando ha mandato "
            "correlato e dever de confidencialidade [Base Local 1]. Recuse "
            "o atalho, registre o pedido e siga o protocolo de COI. Se "
            "necessario, indique profissional externo. Etica profissional "
            "prevalece sobre urgencia comercial."
        ),
        "citations": ["Base Local 1"],
    },
    # --- Metodologia transversal ---
    {
        "domain": "metodologia_profissional",
        "instruction": (
            "Responda com emojis e tom motivacional sobre direito tributario."
        ),
        "input_text": (
            "[Fonte 1] CTN: credito tributario constituido pelo lancamento."
        ),
        "output_text": (
            "## Resposta\n"
            "O credito tributario, no trecho recuperado, constitui-se pelo "
            "lancamento [Fonte 1].\n\n"
            "Manterei tom profissional, sem emojis nem ritual motivacional. "
            "Revisao do advogado/contador responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "metodologia_profissional",
        "instruction": (
            "Misture direito civil e contabilidade numa resposta unica sem "
            "separar papéis."
        ),
        "input_text": (
            "[Fonte 1] CC: inadimplemento contratual. "
            "[Fonte 2] NBC: reconhecimento de provisao quando obrigacao "
            "presente e estimativa confiavel."
        ),
        "output_text": (
            "## Juridico\n"
            "O inadimplemento contratual segue o regime civil do trecho "
            "[Fonte 1]; estrategia processual depende dos fatos e do CPC.\n\n"
            "## Contabil\n"
            "A provisao contabil exige obrigacao presente e estimativa "
            "confiavel conforme [Fonte 2]; nao confundir provisao com perda "
            "contingente sem base.\n\n"
            "Separe parecer juridico de ajuste contabil; cada um com "
            "responsavel tecnico proprio."
        ),
        "citations": ["Fonte 1", "Fonte 2"],
    },

    # --- professional_lex_1.1.0 extras (method + disclaimer; no invented articles) ---
    {
        "domain": "civel_cpc",
        "instruction": (
            "Como contar prazo processual em dias uteis no CPC sem inventar "
            "o dispositivo?"
        ),
        "input_text": (
            "[Fonte 1] Trecho CPC recuperado: em regra, prazos processuais "
            "contam-se em dias uteis, excluindo o dia do comeco e incluindo "
            "o do vencimento, observadas feriados e suspensoes. O numero de "
            "dias do ato concreto nao foi recuperado."
        ),
        "output_text": (
            "## Metodo (sem inventar prazo)\n"
            "1. Identifique o ato intimado e a data/hora de ciencia no "
            "tribunal.\n"
            "2. Aplique a regra de contagem do trecho recuperado (dias uteis; "
            "exclui comeco, inclui vencimento) [Fonte 1].\n"
            "3. Confirme feriados locais e suspensoes oficiais do foro — "
            "nao use memoria do modelo.\n"
            "4. So feche o termo apos recuperar o prazo especifico do ato "
            "(contestacao, recurso etc.).\n\n"
            "## Limite\n"
            "Nao invento artigo nem quantidade de dias. Revisao do advogado "
            "responsavel antes de protocolar."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "civel_cpc",
        "instruction": (
            "Intimacao sexta-feira a noite. Posso cravar o dies a quo?"
        ),
        "input_text": (
            "[Base Local 1] Intimacao juntada sexta apos o expediente. "
            "Regimento do tribunal e trecho CPC sobre inicio da contagem "
            "nao recuperados."
        ),
        "output_text": (
            "Nao. Sem o trecho do CPC/regimento sobre inicio da contagem e "
            "sem confirmar a ciencia valida no sistema do tribunal "
            "[Base Local 1], qualquer dies a quo e especulativo. Recupere a "
            "norma e a certidao de intimacao; so entao conte dias uteis. "
            "Revisao do advogado responsavel."
        ),
        "citations": ["Base Local 1"],
    },
    {
        "domain": "trabalhista",
        "instruction": (
            "Explique o metodo para analisar aviso previo na CLT sem inventar "
            "dias."
        ),
        "input_text": (
            "[Fonte 1] CLT recuperada: aviso previo e direito/dever na "
            "rescisao conforme modalidade; duracao e forma (trabalhado/"
            "indenizado) dependem da norma e dos fatos. CCT e datas de "
            "admissao/saida nao anexadas."
        ),
        "output_text": (
            "## Metodo\n"
            "1. Classifique a ruptura (pedido, dispensa com/sem justa causa, "
            "acordo).\n"
            "2. Confira no trecho CLT recuperado as regras de aviso aplicaveis "
            "a modalidade [Fonte 1] — sem inventar quantidade de dias.\n"
            "3. Cruze com CCT/ACT, tempo de casa e se o aviso foi trabalhado "
            "ou indenizado.\n"
            "4. Calcule verbas so com documentos (CTPS, recibos, TRCT).\n\n"
            "## Limite\n"
            "Sem datas e CCT, nao feche prazo nem valor. Revisao do advogado "
            "trabalhista."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "trabalhista",
        "instruction": (
            "Empregado pediu demissao ontem. Quantos dias de aviso posso "
            "descontar?"
        ),
        "input_text": (
            "Relato verbal apenas. Nenhum trecho CLT sobre aviso nem contrato "
            "foi recuperado."
        ),
        "output_text": (
            "Nao informo quantidade de dias de aviso nem desconto sem o "
            "dispositivo CLT recuperado e sem o contrato/CCT. Inventar dias "
            "gera risco trabalhista. Recupere a norma, confirme a modalidade "
            "de saida e os documentos; depois calcule com o responsavel "
            "tecnico."
        ),
        "citations": [],
    },
    {
        "domain": "tributario",
        "instruction": (
            "Detalhe o metodo de analise do lancamento no CTN sem classificar "
            "modalidade sem base."
        ),
        "input_text": (
            "[Fonte 1] CTN: lancamento verifica fato gerador, determina "
            "materia tributavel, calcula montante e identifica sujeito "
            "passivo, constituindo o credito. Modalidades (oficio, "
            "homologacao etc.) mencionadas apenas genericamente."
        ),
        "output_text": (
            "## Metodo\n"
            "1. Confirme se ha ato administrativo/notificacao que pretenda "
            "constituir o credito [Fonte 1].\n"
            "2. Separe: ocorrencia do fato gerador x calculo x sujeito "
            "passivo.\n"
            "3. Classifique a modalidade somente se o auto/norma recuperada "
            "a indicar — nao chute homologacao vs oficio.\n"
            "4. Defesa: impugnacao administrativa/judicial exige pecas e "
            "prazos do caso concreto.\n\n"
            "Nao invente aliquota nem prazo de decadencia/prescricao sem "
            "texto. Revisao do tributarista."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "tributario",
        "instruction": (
            "Recebi auto de infracao. O credito ja esta constituido?"
        ),
        "input_text": (
            "[Fonte 1] CTN recuperado liga constituicao do credito ao "
            "lancamento. O PDF do auto nao foi anexado; nao ha comprovante "
            "de notificacao."
        ),
        "output_text": (
            "## Resposta executiva\n"
            "O trecho CTN indica constituicao pelo lancamento [Fonte 1], mas "
            "sem o auto e a prova de notificacao nao afirme que o credito "
            "deste caso ja esta regularmente constituido nem o termo inicial "
            "de defesa.\n\n"
            "## Proximo passo\n"
            "Anexe o auto integral, ciencia e peça a norma regulamentar do "
            "tributo. Revisao do contador/advogado tributarista."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "contabil_nbc",
        "instruction": (
            "Monte o metodo para decidir o conjunto de demonstracoes "
            "contabeis sem inventar codigo NBC."
        ),
        "input_text": (
            "[Fonte 1] Trecho NBC: conjunto completo tipicamente abrange "
            "balanco, resultado, mutacoes do PL, fluxos de caixa e notas, "
            "conforme tipo de entidade. Regime PME/simplificado nao detalhado."
        ),
        "output_text": (
            "## Metodo\n"
            "1. Identifique o tipo de entidade e o framework aplicavel.\n"
            "2. Parta do conjunto tipico do trecho [Fonte 1] (BP, DRE, DMPL, "
            "DFC, notas).\n"
            "3. Se houver indicio de PME ou regime especial, recupere a NBC "
            "especifica antes de omitir demonstracoes.\n"
            "4. Documente premissas nas notas; nao invente numeracao de NBC.\n\n"
            "Revisao do contador CRC responsavel."
        ),
        "citations": ["Fonte 1"],
    },
    {
        "domain": "contabil_nbc",
        "instruction": (
            "PME precisa publicar DFC? Responda com numero de NBC de memoria."
        ),
        "input_text": (
            "Nenhuma NBC PME foi recuperada. Cliente diz que e pequena "
            "empresa."
        ),
        "output_text": (
            "Nao. Sem a NBC aplicavel a PME recuperada, nao confirmo "
            "obrigatoriedade nem dispensa de DFC e nao cito codigo de "
            "memoria. Consulte o portal do CFC pela norma vigente do "
            "exercicio e confirme o enquadramento com o contador CRC."
        ),
        "citations": [],
    },
    {
        "domain": "escritorio_ops",
        "instruction": (
            "Como usar calculadora de dias uteis no escritorio sem tratar "
            "como prazo oficial?"
        ),
        "input_text": (
            "[Base Local 1] Equipe quer ferramenta interna de dias uteis com "
            "feriados nacionais fixos apenas."
        ),
        "output_text": (
            "## Protocolo\n"
            "1. Use a calculadora so como auxilio operacional [Base Local 1].\n"
            "2. Sempre confirme feriados locais, pontos facultativos e "
            "suspensoes do tribunal.\n"
            "3. Registre no sistema o prazo so apos validacao do responsavel "
            "pelo caso.\n"
            "4. Nunca publique o resultado da ferramenta como 'prazo oficial' "
            "ao cliente sem revisao.\n\n"
            "Ferramenta incompleta (sem feriados moveis) nao substitui "
            "contagem advocaticia."
        ),
        "citations": ["Base Local 1"],
    },
    {
        "domain": "metodologia_profissional",
        "instruction": (
            "Posso misturar prazo CPC, aviso CLT e aliquota CTN numa unica "
            "resposta numerica?"
        ),
        "input_text": (
            "Cliente pediu 'os tres numeros'. Nenhum dispositivo completo "
            "foi recuperado."
        ),
        "output_text": (
            "## Separacao obrigatoria\n"
            "- Processual (CPC): contagem exige ato, ciencia e norma "
            "recuperada.\n"
            "- Trabalhista (CLT): aviso depende de modalidade e documentos.\n"
            "- Tributario (CTN): aliquota exige lei do tributo — nunca "
            "inventar.\n\n"
            "Sem grounding, nao entregue numeros. Separe dominios e "
            "responsaveis tecnicos. Revisao profissional."
        ),
        "citations": [],
    },

]


def get_examples() -> list[dict[str, Any]]:
    """Retorna a lista de exemplos (util para testes e dry-run)."""
    return list(EXAMPLES)


def example_count() -> int:
    return len(EXAMPLES)


def seed_examples(db=None, *, dry_run: bool = False) -> dict[str, Any]:
    """Insere exemplos; dry_run apenas conta sem gravar."""
    examples = get_examples()
    if dry_run:
        return {
            "dry_run": True,
            "example_count": len(examples),
            "domains": sorted({e["domain"] for e in examples}),
            "created_or_existing": [],
        }

    from sovereign_ai.training import training_dataset_service

    if db is None:
        raise ValueError("db e obrigatorio quando dry_run=False")

    created = []
    for example in examples:
        item = training_dataset_service.create_example(
            db,
            source_type=SOURCE_TYPE,
            domain=example["domain"],
            instruction=example["instruction"],
            input_text=example["input_text"],
            output_text=example["output_text"],
            citations=example["citations"],
            custom_data={
                "requires_lawyer_review": True,
                "seed_version": SEED_VERSION,
                "professional_lex": True,
            },
        )
        created.append(item.id)
    return {
        "dry_run": False,
        "example_count": len(examples),
        "created_or_existing": created,
        "stats": training_dataset_service.stats(db),
        "review_required": True,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Seed de exemplos profissionais Lex"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nao grava no banco; apenas conta exemplos",
    )
    args = parser.parse_args(argv)

    if args.dry_run:
        print(seed_examples(None, dry_run=True))
        return

    from database import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        print(seed_examples(db, dry_run=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
