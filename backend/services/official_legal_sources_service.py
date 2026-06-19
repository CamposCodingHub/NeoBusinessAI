"""Selecao e recuperacao de fontes juridicas oficiais brasileiras."""

from __future__ import annotations

import io
import re
import time
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Dict, List, Optional

import requests

try:
    from pypdf import PdfReader

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).lower()


class PlainTextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: List[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs):
        if tag in {"script", "style", "nav", "footer"}:
            self._ignored_depth += 1
        elif tag in {"p", "br", "div", "li", "tr", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str):
        if tag in {"script", "style", "nav", "footer"} and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str):
        if not self._ignored_depth:
            self.parts.append(data)

    def text(self) -> str:
        raw = " ".join(self.parts)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n\s*\n+", "\n", raw)
        return raw.strip()


@dataclass(frozen=True)
class OfficialLegalSource:
    code: str
    title: str
    url: str
    legal_area: str
    aliases: tuple[str, ...]
    source_type: str = "legislation"


LEGAL_SOURCES = (
    OfficialLegalSource(
        "CF88",
        "Constituicao da Republica Federativa do Brasil de 1988",
        "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm",
        "constitucional",
        ("constituicao", "constitucional", "cf/88", "direitos fundamentais"),
    ),
    OfficialLegalSource(
        "CP",
        "Codigo Penal - Decreto-Lei 2.848/1940",
        "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm",
        "penal",
        (
            "codigo penal",
            "direito penal",
            "crime",
            "pena",
            "tipicidade",
            "dolo",
            "culpa",
            "homicidio",
            "furto",
            "roubo",
            "estelionato",
            "legitima defesa",
            "concurso de pessoas",
        ),
    ),
    OfficialLegalSource(
        "CPP",
        "Codigo de Processo Penal - Decreto-Lei 3.689/1941",
        "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm",
        "processual_penal",
        (
            "codigo de processo penal",
            "processo penal",
            "inquerito",
            "prisao",
            "habeas corpus",
            "acao penal",
            "denuncia",
            "prova penal",
            "audiencia de custodia",
        ),
    ),
    OfficialLegalSource(
        "CC",
        "Codigo Civil - Lei 10.406/2002",
        "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
        "civil",
        (
            "codigo civil",
            "direito civil",
            "contrato",
            "obrigacao",
            "responsabilidade civil",
            "dano moral contratual",
            "inadimplemento contratual",
            "prescricao",
            "posse",
            "propriedade",
            "familia",
            "sucessao",
        ),
    ),
    OfficialLegalSource(
        "CPC",
        "Codigo de Processo Civil - Lei 13.105/2015",
        "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm",
        "processual_civil",
        (
            "codigo de processo civil",
            "processo civil",
            "cpc",
            "recurso",
            "contestacao",
            "peticao inicial",
            "tutela de urgencia",
            "cumprimento de sentenca",
            "execucao",
        ),
    ),
    OfficialLegalSource(
        "CLT",
        "Consolidacao das Leis do Trabalho",
        "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm",
        "trabalhista",
        (
            "clt",
            "trabalhista",
            "empregado",
            "empregador",
            "rescisao trabalhista",
            "justa causa",
        ),
    ),
    OfficialLegalSource(
        "CDC",
        "Codigo de Defesa do Consumidor - Lei 8.078/1990",
        "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm",
        "consumidor",
        (
            "codigo de defesa do consumidor",
            "cdc",
            "consumidor",
            "fornecedor",
            "vicio oculto",
            "vicio do produto",
            "fato do produto",
            "defeito do produto",
        ),
    ),
    OfficialLegalSource(
        "LGPD",
        "Lei Geral de Protecao de Dados - Lei 13.709/2018",
        "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
        "proteção_de_dados",
        ("lgpd", "dados pessoais", "proteção de dados", "tratamento de dados"),
    ),
    OfficialLegalSource(
        "ECA",
        "Estatuto da Crianca e do Adolescente - Lei 8.069/1990",
        "https://www.planalto.gov.br/ccivil_03/leis/l8069.htm",
        "infancia",
        ("eca", "crianca", "adolescente", "ato infracional"),
    ),
    OfficialLegalSource(
        "CTN",
        "Codigo Tributario Nacional - Lei 5.172/1966",
        "https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm",
        "tributario",
        ("ctn", "tributario", "tributo", "imposto", "credito tributario"),
    ),
    OfficialLegalSource(
        "RFB_IRPF2026",
        "Receita Federal - Perguntas e Respostas IRPF 2026",
        (
            "https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/"
            "publicacoes/perguntas-e-respostas/dirpf/"
            "p-r-irpf-2026-v1-00-2026-04-23.pdf"
        ),
        "contabil_fiscal",
        (
            "irpf 2026",
            "imposto de renda 2026",
            "declaracao de imposto de renda",
            "ganho de capital",
            "dependente",
            "rendimento tributavel",
            "malha fiscal",
        ),
        "official_pdf",
    ),
    OfficialLegalSource(
        "RFB_DCTFWEB",
        "Receita Federal - DCTFWeb",
        (
            "https://www.gov.br/receitafederal/pt-br/assuntos/"
            "orientacao-tributaria/declaracoes-e-demonstrativos/DCTFWeb"
        ),
        "contabil_fiscal",
        (
            "dctfweb",
            "mit",
            "darf previdenciario",
            "per/dcomp",
            "declaracao de debitos",
            "obrigacao acessoria",
        ),
        "official_guidance",
    ),
    OfficialLegalSource(
        "ESOCIAL",
        "eSocial - Perguntas Frequentes para Empresas",
        "https://www.gov.br/esocial/pt-br/empresas/perguntas-frequentes",
        "trabalhista_previdenciario",
        (
            "esocial",
            "folha de pagamento",
            "admissao",
            "afastamento",
            "desligamento",
            "sst",
            "evento periodico",
            "evento nao periodico",
        ),
        "official_guidance",
    ),
    OfficialLegalSource(
        "CFC_NBC",
        "Conselho Federal de Contabilidade - Normas Brasileiras de Contabilidade",
        "https://cfc.org.br/tecnica/normas-brasileiras-de-contabilidade/",
        "contabil",
        (
            "norma brasileira de contabilidade",
            "nbc",
            "itg 2000",
            "balanco patrimonial",
            "demonstracoes contabeis",
            "lancamento contabil",
            "contador",
            "contabilidade",
        ),
        "official_guidance",
    ),
    OfficialLegalSource(
        "CFC_ESCRITURACAO",
        "CFC - Obrigatoriedade de Escrituracao Contabil",
        (
            "https://cfc.org.br/tecnica/perguntas-frequentes/"
            "obrigatoriedade-de-escrituracao-contabil/"
        ),
        "contabil",
        (
            "escrituracao contabil",
            "livro diario",
            "livro razao",
            "dispensa de contabilidade",
            "simples nacional contabilidade",
        ),
        "official_guidance",
    ),
    OfficialLegalSource(
        "RFB_RTC2026",
        "Receita Federal - Orientacoes da Reforma Tributaria do Consumo em 2026",
        (
            "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/"
            "acoes-e-programas/programas-e-atividades/"
            "reforma-tributaria-do-consumo/orientacoes-2026"
        ),
        "tributario_reforma_consumo",
        (
            "reforma tributaria 2026",
            "ibs",
            "cbs",
            "imposto seletivo",
            "documento fiscal 2026",
            "tributacao do consumo",
        ),
        "official_guidance",
    ),
    OfficialLegalSource(
        "CNJ_DOMICILIO",
        "CNJ - Domicilio Judicial Eletronico: Perguntas Frequentes",
        (
            "https://www.cnj.jus.br/tecnologia-da-informacao-e-comunicacao/"
            "justica-4-0/domicilio-judicial-eletronico/perguntas-frequentes/"
        ),
        "processual_comunicacoes",
        (
            "domicilio judicial eletronico",
            "citacao eletronica",
            "comunicacao processual",
            "prazo no domicilio judicial",
            "intimacao eletronica",
        ),
        "official_guidance",
    ),
    OfficialLegalSource(
        "EOAB",
        "Estatuto da Advocacia e da OAB - Lei 8.906/1994",
        "https://www.planalto.gov.br/ccivil_03/leis/l8906.htm",
        "advocacia",
        ("estatuto da oab", "oab", "honorarios advocaticios", "advocacia"),
    ),
    OfficialLegalSource(
        "STF",
        "Pesquisa de Jurisprudencia do STF",
        "https://portal.stf.jus.br/jurisprudencia/",
        "jurisprudencia",
        ("stf", "supremo", "repercussao geral", "controle de constitucionalidade"),
        "jurisprudence_portal",
    ),
    OfficialLegalSource(
        "STJ",
        "Acordaos e Decisoes do STJ",
        "https://www.stj.jus.br/sites/portalp/Jurisprudencia/Acordaos-e-Decisoes",
        "jurisprudencia",
        ("stj", "superior tribunal de justica", "recurso especial", "repetitivo"),
        "jurisprudence_portal",
    ),
    OfficialLegalSource(
        "TST",
        "Pesquisa de Jurisprudencia do Tribunal Superior do Trabalho",
        "https://jurisprudencia.tst.jus.br/",
        "jurisprudencia_trabalhista",
        (
            "tst",
            "tribunal superior do trabalho",
            "jurisprudencia trabalhista",
            "imediatidade",
            "proporcionalidade",
        ),
        "jurisprudence_portal",
    ),
    OfficialLegalSource(
        "ANPD",
        "Agencia Nacional de Protecao de Dados",
        "https://www.gov.br/anpd/pt-br",
        "protecao_de_dados",
        (
            "anpd",
            "guia da anpd",
            "regulamento da anpd",
            "autoridade nacional de protecao de dados",
        ),
        "official_guidance",
    ),
    OfficialLegalSource(
        "CARF",
        "Pesquisa de Acordaos do CARF",
        "https://carf.economia.gov.br/jurisprudencia/acordaos-carf-2",
        "tributario_administrativo",
        (
            "carf",
            "conselho administrativo de recursos fiscais",
            "acordao do carf",
        ),
        "jurisprudence_portal",
    ),
    OfficialLegalSource(
        "DATAJUD",
        "API Publica DataJud - Conselho Nacional de Justica",
        "https://datajud-wiki.cnj.jus.br/api-publica/",
        "dados_processuais",
        ("datajud", "andamento processual", "movimentacao processual", "processo judicial"),
        "official_data",
    ),
)

TOPIC_ARTICLE_HINTS = {
    "CP": (
        (("dolo", "culpa"), ("18",)),
        (("homicidio",), ("121",)),
        (("legitima defesa",), ("23", "25")),
        (("concurso de pessoas",), ("29", "30", "31")),
        (("furto",), ("155",)),
        (("roubo",), ("157",)),
        (("estelionato",), ("171",)),
    ),
    "CPP": (
        (("prisao preventiva", "preventiva"), ("282", "312", "313", "315", "319")),
        (("audiencia de custodia",), ("310",)),
        (("prova",), ("155", "156", "157")),
        (("inquerito",), ("4", "5", "10")),
    ),
    "CPC": (
        (
            ("tutela de urgencia", "tutela da evidencia", "tutela cautelar"),
            ("294", "297", "300", "301", "302", "303", "304", "305", "311"),
        ),
        (("contestacao",), ("335", "336", "337", "341")),
        (("peticao inicial",), ("319", "320", "321", "330")),
        (("cumprimento de sentenca",), ("513", "523", "525")),
    ),
    "CC": (
        (
            ("inadimplemento", "perdas e danos", "clausula penal"),
            (
                "389",
                "393",
                "395",
                "402",
                "403",
                "408",
                "409",
                "412",
                "413",
                "475",
                "478",
                "479",
                "480",
            ),
        ),
        (("prescricao",), ("189", "205", "206")),
        (("responsabilidade civil",), ("186", "187", "927", "944")),
    ),
    "CDC": (
        (
            ("vicio", "fato do produto", "defeito"),
            ("12", "13", "14", "18", "20", "26", "27", "51"),
        ),
        (("oferta",), ("30", "35")),
        (("pratica abusiva",), ("39",)),
    ),
    "CLT": (
        (("justa causa",), ("482", "818")),
        (("jornada", "hora extra"), ("58", "59", "71", "74")),
        (("rescisao",), ("477", "482", "483")),
    ),
    "LGPD": (
        (
            ("consentimento", "execucao de contrato", "legitimo interesse", "base legal"),
            ("6", "7", "8", "10", "11", "42", "46"),
        ),
        (("incidente", "seguranca"), ("46", "48", "49")),
        (("direitos do titular",), ("18", "19")),
    ),
}

VERIFIED_TOPIC_GUARDRAILS = {
    "CP": (
        (
            ("dolo", "culpa"),
            (
                "O art. 18, I, define dolo como querer o resultado ou assumir o "
                "risco de produzi-lo. O inciso II define culpa por imprudencia, "
                "negligencia ou impericia. A distincao entre dolo eventual e culpa "
                "consciente exige interpretacao doutrinaria e jurisprudencial, nao "
                "esta integralmente definida no texto do art. 18."
            ),
        ),
    ),
    "CPP": (
        (
            ("prisao preventiva", "preventiva"),
            (
                "Nao trate gravidade abstrata como fundamento automatico. O art. "
                "312 exige prova da existencia do crime, indicio suficiente de "
                "autoria e perigo gerado pela liberdade, ligado a garantia da ordem "
                "publica ou economica, conveniencia da instrucao criminal ou "
                "aplicacao da lei penal. Confira tambem admissibilidade no art. "
                "313, fundamentacao concreta no art. 315, criterios do art. 282 e "
                "alternativas do art. 319. A regra de que preventiva so cabe quando "
                "nao for possivel substitui-la por cautelar diversa esta no art. "
                "282, par. 6; nao a atribua ao caput do art. 312."
            ),
        ),
    ),
    "CPC": (
        (
            ("tutela de urgencia", "tutela da evidencia", "tutela cautelar"),
            (
                "O art. 300 exige probabilidade do direito e perigo de dano ou "
                "risco ao resultado util tanto para tutela antecipada de urgencia "
                "quanto para tutela cautelar de urgencia. Tutela antecipada nao deve "
                "ser concedida quando houver perigo de irreversibilidade. O art. 311 disciplina "
                "tutela da evidencia e dispensa perigo de dano apenas nas hipoteses "
                "legais; nao atribua esse regime a dispositivos de outras secoes."
            ),
        ),
    ),
    "CC": (
        (
            ("inadimplemento", "perdas e danos", "clausula penal"),
            (
                "Use os arts. 389, 402 e 403 para perdas e danos; arts. 408, 412 e "
                "413 para clausula penal; e art. 475 para resolucao ou exigencia de "
                "cumprimento com perdas e danos. Nao use como base dispositivo "
                "revogado do Codigo de Processo Civil anterior."
            ),
        ),
    ),
    "CDC": (
        (
            ("vicio", "fato do produto", "defeito"),
            (
                "Nao confunda tres prazos: o art. 18, par. 1, concede em regra 30 "
                "dias para o fornecedor sanar o vicio; o art. 26 preve decadencia "
                "de 30 dias para produto/servico nao duravel e 90 dias para duravel, "
                "e, no vicio oculto, o par. 3 determina que o prazo se inicia "
                "quando ficar evidenciado o defeito; o art. 27 preve cinco anos "
                "para reparacao por dano decorrente de fato do produto/servico. "
                "Vicio afeta adequacao, qualidade, quantidade ou valor; fato do "
                "produto envolve dano causado por defeito de seguranca. No fato do "
                "produto, comerciante responde nas hipoteses especificas do art. 13; "
                "nao apresente solidariedade geral sem essa ressalva."
            ),
        ),
    ),
    "CLT": (
        (
            ("justa causa",),
            (
                "O art. 482 enumera hipoteses de justa causa e o art. 818 trata do "
                "onus da prova. Imediatidade, proporcionalidade, non bis in idem e "
                "gradacao sao criterios interpretativos/jurisprudenciais; nao diga "
                "que dispositivos sobre estabilidade criam investigacao previa "
                "geral, contraditorio ou ampla defesa para todo empregado."
            ),
        ),
    ),
    "LGPD": (
        (
            ("consentimento", "execucao de contrato", "legitimo interesse", "base legal"),
            (
                "O art. 7 lista bases para dados pessoais, incluindo consentimento, "
                "obrigacao legal, execucao de contrato e legitimo interesse. O art. "
                "8 disciplina consentimento. O art. 10 exige finalidade legitima, "
                "necessidade e transparencia no legitimo interesse. Dados pessoais "
                "sensiveis seguem as hipoteses especificas do art. 11."
            ),
        ),
    ),
}


class OfficialLegalSourcesService:
    def __init__(self, cache_ttl_seconds: int = 21600):
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, tuple[float, str]] = {}

    def analyze_query(self, query: str) -> Dict[str, object]:
        normalized = normalize_text(query)
        article_match = re.search(
            r"\bart(?:igo)?\.?\s*(\d+[a-z]?(?:-[a-z])?)",
            normalized,
        )
        selected = []
        scores: Dict[str, int] = {}

        for source in LEGAL_SOURCES:
            score = 0
            for alias in source.aliases:
                normalized_alias = normalize_text(alias)
                if not re.search(
                    rf"(?<!\w){re.escape(normalized_alias)}(?!\w)",
                    normalized,
                ):
                    continue
                score += 3 if " " in normalized_alias else 2

            explicit_codes = {
                "CF88": ("cf/88", "cf88"),
                "CPP": ("cpp",),
                "CC": ("cc",),
                "CPC": ("cpc",),
                "CLT": ("clt",),
                "CDC": ("cdc",),
                "LGPD": ("lgpd",),
                "ECA": ("eca",),
                "CTN": ("ctn",),
                "EOAB": ("oab",),
                "STF": ("stf",),
                "STJ": ("stj",),
                "TST": ("tst",),
                "ANPD": ("anpd",),
                "CARF": ("carf",),
                "DATAJUD": ("datajud",),
                "RFB_IRPF2026": ("irpf",),
                "RFB_DCTFWEB": ("dctfweb", "mit"),
                "ESOCIAL": ("esocial",),
                "CFC_NBC": ("nbc", "cfc"),
                "CFC_ESCRITURACAO": ("escrituracao contabil",),
                "RFB_RTC2026": ("ibs", "cbs"),
                "CNJ_DOMICILIO": ("domicilio judicial eletronico",),
            }
            if any(
                re.search(rf"(?<!\w){re.escape(code)}(?!\w)", normalized)
                for code in explicit_codes.get(source.code, ())
            ):
                score += 5
            if source.code == "STF" and "constitucional" in normalized:
                score += 1
            if source.code == "STJ" and any(
                term in normalized
                for term in ("jurisprudencia", "entendimento", "precedente")
            ):
                score += 1
            if score:
                scores[source.code] = score

        if scores:
            highest_score = max(scores.values())
            minimum_score = max(2, highest_score - 1)
            ordered_codes = sorted(
                (
                    code
                    for code, score in scores.items()
                    if score >= minimum_score
                ),
                key=scores.get,
                reverse=True,
            )
            selected = [
                source
                for code in ordered_codes
                for source in LEGAL_SOURCES
                if source.code == code
            ][:4]
        elif area_match := re.search(
            r"area juridica em continuidade:\s*([a-z_]+)",
            normalized,
        ):
            continued_area = area_match.group(1)
            selected = [
                source
                for source in LEGAL_SOURCES
                if normalize_text(source.legal_area) == continued_area
                and source.source_type == "legislation"
            ][:2]
        elif any(
            re.search(pattern, normalized)
            for pattern in (
                r"\bcontab\w*",
                r"\bfiscal\w*",
                r"\btribut\w*",
                r"\bprevidenci\w*",
            )
        ):
            selected = [
                source
                for source in LEGAL_SOURCES
                if source.code in {"CFC_NBC", "RFB_DCTFWEB", "CTN"}
            ]
        elif any(
            re.search(pattern, normalized)
            for pattern in (
                r"\blei\b",
                r"\bjuridic\w*",
                r"\badvog\w*",
                r"\btribunal\w*",
                r"\bprocess\w*",
            )
        ):
            selected = [
                source
                for source in LEGAL_SOURCES
                if source.code in {"CF88", "CPC", "STJ"}
            ]

        if "esocial" in normalized and any(
            term in normalized
            for term in (
                "justa causa",
                "rescisao",
                "dispensa",
                "empregado",
                "trabalhista",
            )
        ):
            clt_source = next(
                source for source in LEGAL_SOURCES if source.code == "CLT"
            )
            if all(source.code != "CLT" for source in selected):
                selected = [*selected, clt_source][:4]

        primary_area = selected[0].legal_area if selected else "geral"
        return {
            "is_legal_query": bool(selected),
            "legal_area": primary_area,
            "article": article_match.group(1) if article_match else None,
            "sources": selected,
        }

    def retrieve(self, query: str, max_sources: int = 4) -> Dict[str, object]:
        analysis = self.analyze_query(query)
        selected_sources: List[OfficialLegalSource] = list(
            analysis["sources"]
        )[:max_sources]
        results = []

        for source in selected_sources:
            excerpt = ""
            fetch_status = "link_only"
            if source.source_type in {
                "legislation",
                "official_guidance",
                "official_pdf",
            }:
                try:
                    text = self._fetch_text(source.url)
                    if source.source_type == "legislation":
                        hinted_articles = self._hint_articles(source.code, query)
                        if analysis.get("article"):
                            hinted_articles = tuple(
                                dict.fromkeys(
                                    (str(analysis["article"]), *hinted_articles)
                                )
                            )
                        excerpt = (
                            self._extract_article_blocks(text, hinted_articles)
                            if hinted_articles
                            else self._extract_relevant_excerpt(text, query)
                        )
                    else:
                        excerpt = self._extract_relevant_excerpt(text, query)
                    fetch_status = "official_text" if excerpt else "link_only"
                except Exception:
                    fetch_status = "unavailable"

            results.append(
                {
                    "code": source.code,
                    "title": source.title,
                    "url": source.url,
                    "legal_area": source.legal_area,
                    "source_type": source.source_type,
                    "excerpt": excerpt,
                    "status": fetch_status,
                }
            )

        grounded_sources = [
            source for source in results if source["status"] == "official_text"
        ]
        return {
            "is_legal_query": analysis["is_legal_query"],
            "legal_area": analysis["legal_area"],
            "article": analysis["article"],
            "sources": results,
            "grounding_status": (
                "official_sources"
                if grounded_sources
                else "official_links"
                if results
                else "unverified"
            ),
            "guardrails": self._collect_guardrails(query, selected_sources),
        }

    def build_context(self, retrieval: Dict[str, object]) -> str:
        source_blocks = []
        guardrails = retrieval.get("guardrails", [])
        if guardrails:
            source_blocks.append(
                "REGRAS FACTUAIS CURADAS PARA ESTA CONSULTA:\n- "
                + "\n- ".join(str(item) for item in guardrails)
            )
        for index, source in enumerate(retrieval.get("sources", []), start=1):
            block = [
                f"[Fonte {index}] {source['title']}",
                f"URL oficial: {source['url']}",
            ]
            if source.get("excerpt"):
                block.append(f"Trecho oficial:\n{source['excerpt']}")
            else:
                block.append(
                    "Texto integral nao recuperado nesta execucao; use o link oficial para verificacao."
                )
                if source.get("source_type") == "jurisprudence_portal":
                    block.append(
                        "Nenhuma decisao, ementa ou tese foi recuperada. Nao "
                        "atribua entendimento ao tribunal e nao confirme numero "
                        "de processo com base apenas neste portal."
                    )
            source_blocks.append("\n".join(block))
        return "\n\n".join(source_blocks)

    def _collect_guardrails(
        self,
        query: str,
        selected_sources: List[OfficialLegalSource],
    ) -> List[str]:
        normalized_query = normalize_text(query)
        guardrails = []
        for source in selected_sources:
            for terms, instruction in VERIFIED_TOPIC_GUARDRAILS.get(
                source.code,
                (),
            ):
                if any(
                    normalize_text(term) in normalized_query
                    for term in terms
                ):
                    guardrails.append(instruction)
        return guardrails

    def _hint_articles(self, source_code: str, query: str) -> tuple[str, ...]:
        normalized_query = normalize_text(query)
        for terms, articles in TOPIC_ARTICLE_HINTS.get(source_code, ()):
            if any(normalize_text(term) in normalized_query for term in terms):
                return articles
        return ()

    def _extract_article_blocks(
        self,
        text: str,
        articles: tuple[str, ...],
        max_characters_per_article: int = 2600,
    ) -> str:
        blocks = []

        for article in articles:
            match = self._find_article_heading(text, article)
            if not match:
                continue
            start = match.start("heading")
            next_article = re.search(
                r"(?m)^[ \t]*Art\.?[ \t]*\d+[a-z]?(?:-[a-z])?"
                r"(?=[ \t]*(?:[.\-–—ºo]|$))",
                text[match.end("heading") :],
            )
            end = (
                match.end("heading") + next_article.start()
                if next_article
                else start + max_characters_per_article
            )
            block = text[start : min(end, start + max_characters_per_article)].strip()
            if block:
                blocks.append(block)

        return "\n\n".join(blocks)[:10000]

    @staticmethod
    def _find_article_heading(text: str, article: str):
        heading_pattern = re.compile(
            rf"(?m)^[ \t]*(?P<heading>Art\.?[ \t]*"
            rf"{re.escape(article)}(?=[ \t]*(?:[.\-–—ºo]|$)))"
        )
        match = heading_pattern.search(text)
        if match:
            return match

        inline_heading = re.search(
            rf"(?P<heading>\bArt\.?[ \t]*"
            rf"{re.escape(article)}(?=[ \t]*(?:[.\-–—ºo]|$)))",
            text,
        )
        if inline_heading:
            return inline_heading

        # Fallback para fontes que publicam todos os cabeçalhos em minúsculas.
        return re.search(
            rf"(?im)^[ \t]*(?P<heading>art\.?[ \t]*"
            rf"{re.escape(article)}(?=[ \t]*(?:[.\-–—ºo]|$)))",
            text,
        )

    def _fetch_text(self, url: str) -> str:
        cached = self._cache.get(url)
        if cached and time.time() - cached[0] < self.cache_ttl_seconds:
            return cached[1]

        response = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.6",
            },
        )
        response.raise_for_status()
        if "planalto.gov.br" in url:
            response.encoding = "ISO-8859-1"
        else:
            response.encoding = response.apparent_encoding or response.encoding
        content_type = response.headers.get("Content-Type", "").lower()
        if "application/pdf" in content_type or url.lower().endswith(".pdf"):
            if not PYPDF_AVAILABLE:
                raise RuntimeError("Leitura de PDF oficial indisponivel")
            reader = PdfReader(io.BytesIO(response.content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            parser = PlainTextHTMLParser()
            parser.feed(response.text)
            text = parser.text()
        self._cache[url] = (time.time(), text)
        return text

    def _extract_relevant_excerpt(
        self,
        text: str,
        query: str,
        article: Optional[str] = None,
        max_characters: int = 6500,
    ) -> str:
        normalized_text = normalize_text(text)

        if article:
            match = self._find_article_heading(text, article)
            if match:
                start = max(0, match.start("heading") - 250)
                return text[start : start + max_characters].strip()

        stop_words = {
            "qual",
            "quais",
            "como",
            "para",
            "sobre",
            "direito",
            "codigo",
            "artigo",
            "uma",
            "que",
            "dos",
            "das",
            "com",
        }
        query_terms = [
            term
            for term in re.findall(r"[a-z0-9]+", normalize_text(query))
            if len(term) >= 4 and term not in stop_words
        ]
        best_position = None
        best_score = 0

        for term in query_terms[:10]:
            position = normalized_text.find(term)
            if position >= 0:
                score = sum(
                    1
                    for other_term in query_terms
                    if other_term in normalized_text[position : position + 3000]
                )
                if score > best_score:
                    best_score = score
                    best_position = position

        if best_position is None:
            return text[:max_characters].strip()

        start = max(0, best_position - 1000)
        return text[start : start + max_characters].strip()


official_legal_sources = OfficialLegalSourcesService()
