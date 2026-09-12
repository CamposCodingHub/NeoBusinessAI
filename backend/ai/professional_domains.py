"""Dominios profissionais da Lex (advocacia + contabilidade/fiscal + ops).

Detectores e addenda de system prompt para orientar respostas sem inventar
aliquotas, prazos fiscais ou pareceres vinculantes.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


PROFESSIONAL_DOMAIN_IDS: Tuple[str, ...] = (
    "trabalhista",
    "civel",
    "tributario",
    "contabil_fiscal",
    "societario",
    "escritorio_ops",
)

# Ordem de desempate quando varios dominios batem (mais especifico primeiro).
_DOMAIN_PRIORITY: Tuple[str, ...] = (
    "contabil_fiscal",
    "tributario",
    "trabalhista",
    "societario",
    "civel",
    "escritorio_ops",
)

SAFE_FISCAL_RULES = """
REGRAS FISCAIS SEGURAS (OBRIGATORIAS):
- Nunca invente aliquota, base de calculo, codigo de receita, leiaute de obrigacao
  acessoria, prazo municipal/estadual ou enquadramento de CNAE/regime sem fonte
  recuperada nesta execucao.
- Se a aliquota ou o tratamento depender de municipio, estado, CNAE, regime
  tributario ou fato concreto ausente, declare a incerteza, cite a ausencia de
  base e liste o que falta para concluir.
- Quando houver duvida, prefira "nao verificado nas fontes recuperadas" a uma
  cifra aproximada.
- Esta orientacao NAO e parecer vinculante, parecer contabil formal nem consulta
  fiscal oficial. Exige revisao do advogado ou contador responsavel antes de
  qualquer ato.
""".strip()

DOMAIN_MARKERS: Dict[str, Tuple[str, ...]] = {
    "trabalhista": (
        "trabalhista",
        "clt",
        "justa causa",
        "rescisao",
        "aviso previo",
        "fgts",
        "horas extras",
        "verbas rescisorias",
        "reclamacao trabalhista",
        "empregado",
        "empregador",
        "trt",
        "tst",
        "contrato de trabalho",
        "estabilidade gestante",
        "intervalo intrajornada",
        "adicional noturno",
        "insalubridade",
        "periculosidade",
        "esocial",
        "folha de pagamento",
    ),
    "civel": (
        "civel",
        "civil",
        "codigo civil",
        "cc/",
        "obrigacao de fazer",
        "indenizacao",
        "danos morais",
        "danos materiais",
        "responsabilidade civil",
        "contrato de prestacao",
        "inadimplemento",
        "mora",
        "prescricao civil",
        "tutela de urgencia",
        "cpc",
        "processo civil",
        "peticao inicial",
        "contestacao",
        "cumprimento de sentenca",
    ),
    "tributario": (
        "tributario",
        "tributaria",
        "tributo",
        "ctn",
        "credito tributario",
        "lancamento tributario",
        "autuacao fiscal",
        "execucao fiscal",
        "carf",
        "compensacao tributaria",
        "imunidade tributaria",
        "isencao tributaria",
        "reforma tributaria",
        "ibs",
        "cbs",
        "imposto seletivo",
    ),
    "contabil_fiscal": (
        "classificacao de despesa",
        "classificar despesa",
        "plano de contas",
        "lancamento contabil",
        "obrigacao acessoria",
        "obrigacoes acessorias",
        "dctf",
        "dctfweb",
        "efd",
        "sped",
        "simples nacional",
        "iss",
        "icms",
        "ipi",
        "irpj",
        "csll",
        "pis",
        "cofins",
        "issqn",
        "guia das",
        "imposto de renda",
        "aliquota",
        "retencao na fonte",
        "nota fiscal",
        "nfe",
        "nfs-e",
        "regime tributario",
        "lucro presumido",
        "lucro real",
        "contabilidade",
        "fiscal",
        "ecd",
        "ecf",
        "das",
        "darf",
        "reinf",
    ),
    "societario": (
        "societario",
        "sociedade limitada",
        "ltda",
        "s.a.",
        "s/a",
        "contrato social",
        "alteracao contratual",
        "quota",
        "quotas",
        "capital social",
        "junta comercial",
        "administrador da sociedade",
        "dissolucao societaria",
        "acordo de socios",
        "acordo de quotistas",
        "holding",
        "m&a",
        "fusao",
        "cisao",
        "incorporacao societaria",
    ),
    "escritorio_ops": (
        "prazo do cliente",
        "meus prazos",
        "controle de prazos",
        "agenda do escritorio",
        "financeiro do escritorio",
        "honorarios",
        "cobranca de cliente",
        "cadastro de cliente",
        "meus clientes",
        "painel do escritorio",
        "operacao do escritorio",
        "rotina do escritorio",
        "status do processo no sistema",
        "lembrete de audiencia",
        "documento no produto",
        "nos meus documentos",
        "meus documentos",
        "meu contrato",
        "o que diz o pdf",
        "busque no documento",
        "procure no documento",
        # Modulos do produto (daytime ops polish)
        "trust accounting",
        "conta trust",
        "valores de clientes",
        "conta de custodia",
        "custodia de valores",
        "e-sign",
        "esign",
        "assinatura eletronica",
        "envelope de assinatura",
        "monitor de intimacoes",
        "monitor de processos",
        "intimacoes no monitor",
        "aging",
        "aging de recebiveis",
        "honorarios em atraso",
        "recebiveis em atraso",
        "nfse stub",
        "nfs-e stub",
        "nfs-e",
        "consentimento whatsapp",
        "whatsapp lgpd",
        "consentimento lgpd whatsapp",
    ),
}

DOMAIN_ADDENDA: Dict[str, str] = {
    "trabalhista": """
ADDENDUM TRABALHISTA:
- Priorize CLT, sumulas/OJs apenas se recuperadas, e fatos do contrato/folha.
- Separe verbas, prazos processuais e riscos de justa causa vs. rescisao sem justa causa.
- Nao invente jurisprudencia do TST/TRT; se ausente, diga que nao foi recuperada.
- Em folha/eSocial, trate como rotina operacional e reforce revisao do responsavel.
""".strip(),
    "civel": """
ADDENDUM CIVEL / PROCESSUAL CIVIL:
- Distinga texto do Codigo Civil/CPC, interpretacao e estrategia processual.
- Indique prescricao/decadencia so com base nas fontes ou declare incerteza.
- Estruture: questao, fundamento, aplicacao, riscos, informacoes faltantes e proximos passos.
- Nao invente numero de processo, precedente ou teor de decisao.
""".strip(),
    "tributario": """
ADDENDUM TRIBUTARIO:
- Trabalhe com CTN, orientacoes oficiais e fatos do credito/autuacao quando houver.
- Diferencie incidencia, nao incidencia, isencao, imunidade e beneficio fiscal.
- Nao invente aliquota, multa, juros ou prazo de defesa/recurso.
- Cite fontes recuperadas; se insuficientes, diga explicitamente e liste o que falta.
""".strip(),
    "contabil_fiscal": """
ADDENDUM CONTABIL / FISCAL OPERACIONAL:
- Oriente classificacao, rotinas e obrigacoes acessorias em nivel de escritorio.
- Confirme regime, periodo, CNPJ/CPF e documentos-fonte antes de concluir.
- Nunca invente aliquota; na duvida, cite a ausencia de base e peca o dado faltante.
- Deixe claro que a resposta nao substitui parecer contabil/fiscal vinculante.
""".strip(),
    "societario": """
ADDENDUM SOCIETARIO:
- Foque em tipo societario, orgaos, capital, alteracoes e formalidades na Junta.
- Distinga regra societaria, efeito tributario e efeito trabalhista quando o caso cruzar areas.
- Nao invente clausulas de contrato social nem exigencias de orgao de registro.
- Liste documentos e atos tipicos (alteracao, ata, procuracao) como checklist, nao como certeza normativa sem fonte.
""".strip(),
    "escritorio_ops": """
ADDENDUM OPERACAO DO ESCRITORIO (PRODUTO):
- Ajude com prazos, clientes, documentos e financeiro operacional com base nos dados/trechos disponiveis.
- Se a pergunta for sobre o acervo do usuario, priorize documentos recuperados no produto.
- Se perguntarem o que da para consultar/fazer no produto, cite de forma objetiva (sem pitch): prazos, matters, intake/COI, time entries, aprovacoes WhatsApp, limites de uso e busca em documentos.
- Quando relevante, cite tambem: trust/valores de clientes (custodia), e-sign/assinatura eletronica (stub), monitor de intimacoes (stub local, nao e DJEn/tribunal real), aging/honorarios em atraso, NFS-e stub (sem prefeitura) e consentimento WhatsApp (LGPD) antes de outbound.
- Tom profissional, sem coach de SaaS, sem emojis e sem pitch comercial.
- Nao invente clausulas, valores, partes ou status ausentes nos dados fornecidos. Nao invente norma.
""".strip(),
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def _marker_matches(normalized: str, marker: str) -> bool:
    needle = normalize_text(marker)
    if not needle:
        return False
    # Marcadores curtos ou facilmente embutidos em outras palavras.
    boundary_markers = {
        "sa",
        "s.a.",
        "s/a",
        "m&a",
        "quota",
        "quotas",
        "cisao",
        "fusao",
        "iss",
        "ipi",
        "pis",
        "nfe",
        "efd",
        "ecd",
        "ecf",
        "das",
        "ibs",
        "cbs",
        "sst",
        "cc/",
    }
    if needle in boundary_markers or len(needle) <= 3:
        pattern = r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])"
        return re.search(pattern, normalized) is not None
    return needle in normalized


def _score_domain(normalized: str, markers: Sequence[str]) -> int:
    score = 0
    for marker in markers:
        if not _marker_matches(normalized, marker):
            continue
        needle = normalize_text(marker)
        # Marcadores compostos pesam mais.
        score += 2 if " " in needle else 1
    return score


def detect_professional_domains(message: str) -> List[str]:
    """Retorna dominios detectados, ordenados por score e prioridade."""
    normalized = normalize_text(message)
    if not normalized:
        return []
    scored: List[Tuple[int, int, str]] = []
    for index, domain_id in enumerate(_DOMAIN_PRIORITY):
        markers = DOMAIN_MARKERS.get(domain_id, ())
        score = _score_domain(normalized, markers)
        if score > 0:
            scored.append((score, -index, domain_id))
    scored.sort(reverse=True)
    return [domain_id for _, _, domain_id in scored]


def primary_professional_domain(
    message: str,
    *,
    fallback: Optional[str] = None,
) -> Optional[str]:
    domains = detect_professional_domains(message)
    if domains:
        return domains[0]
    return fallback


def looks_like_accounting_tax_query(message: str) -> bool:
    """Compativel com internal_document_search: fiscal/contabil operacional."""
    domains = set(detect_professional_domains(message))
    return bool(domains & {"contabil_fiscal", "tributario"})


def looks_like_office_ops_query(message: str) -> bool:
    return "escritorio_ops" in detect_professional_domains(message)


def requires_safe_fiscal_rules(domains: Iterable[str]) -> bool:
    domain_set = set(domains)
    return bool(domain_set & {"contabil_fiscal", "tributario"})


def get_domain_addendum(domain_id: str) -> str:
    return DOMAIN_ADDENDA.get(domain_id, "").strip()


def build_domain_system_addenda(
    domains: Sequence[str],
    *,
    include_safe_fiscal: Optional[bool] = None,
) -> str:
    """Monta bloco de system prompt com addenda dos dominios detectados."""
    unique: List[str] = []
    for domain_id in domains:
        if domain_id in PROFESSIONAL_DOMAIN_IDS and domain_id not in unique:
            unique.append(domain_id)

    blocks: List[str] = []
    for domain_id in unique:
        addendum = get_domain_addendum(domain_id)
        if addendum:
            blocks.append(addendum)

    apply_fiscal = (
        requires_safe_fiscal_rules(unique)
        if include_safe_fiscal is None
        else include_safe_fiscal
    )
    if apply_fiscal:
        blocks.append(SAFE_FISCAL_RULES)

    return "\n\n".join(blocks).strip()


def enrich_detected_area(
    detected_area: Optional[str],
    domains: Sequence[str],
) -> str:
    """Substitui 'geral' pela area profissional primaria quando houver sinal."""
    current = (detected_area or "geral").strip() or "geral"
    if current not in {None, "", "geral"}:
        return current
    for domain_id in domains:
        if domain_id in PROFESSIONAL_DOMAIN_IDS:
            return domain_id
    return current
