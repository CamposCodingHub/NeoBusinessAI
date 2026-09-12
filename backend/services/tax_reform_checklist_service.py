"""
Reforma Tributária / eSocial–DCTFWeb — methodological help checklist.

Static guidance for accountants. NOT legal advice, NOT official RFB calendar,
NO invented tax rates or exact statutory due dates as facts.
"""

from __future__ import annotations

from typing import Any, Dict, List

TAX_REFORM_DISCLAIMER = (
    "LexScan auxilia a rotina operacional. O contador CRC valida, confere e "
    "responde pela entrega. Legislação, leiautes e calendários mudam — confirme "
    "sempre na fonte oficial vigente (RFB, eSocial, comitês IBS/CBS). "
    "Sem alíquotas nem dias de vencimento inventados neste checklist."
)

CHECKLIST_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "esocial_reinf_dctfweb",
        "title": "Cruzamento eSocial × EFD-Reinf × DCTFWeb",
        "summary": (
            "Conferir consistência S-1200/S-1210 (método) antes de fechar "
            "a competência e transmitir débitos."
        ),
        "steps": [
            "Fechar folha e gerar eventos de remuneração (S-1200) com bases e "
            "contribuições coerentes com a política do cliente",
            "Conferir pagamentos / informações de quitação (S-1210) contra "
            "valores já escriturados na remuneração do período",
            "Cruzar totais eSocial com EFD-Reinf (quando houver retenções / "
            "contribuições de responsabilidade de terceiros no escopo)",
            "Só então confrontar débitos previdenciários na DCTFWeb com o "
            "resultado do cruzamento — divergência vira retificação, não "
            "“ajuste na guia” sem trilha",
            "Guardar evidências do cruzamento (relatórios / prints / logs) "
            "para auditoria interna",
        ],
        "method_note": (
            "Método de conferência, não checklist normativo fechado. "
            "Eventos e prazos dependem do calendário e do leiaute oficiais vigentes."
        ),
    },
    {
        "id": "reforma_ibs_cbs",
        "title": "Reforma Tributária — apuração paralela / IBS-CBS em NF",
        "summary": (
            "Preparar apuração paralela e validar campos IBS/CBS em documentos "
            "fiscais conforme calendário oficial vigente (não inventado aqui)."
        ),
        "steps": [
            "Mapear quais clientes entram em transição / obrigação de destaque "
            "IBS-CBS no período (regime e atividade)",
            "Manter apuração paralela (modelo atual × IBS/CBS) enquanto a "
            "transição exigir — sem assumir alíquotas fixas neste guia",
            "Validar no emissor/ERP se os campos IBS/CBS da NF seguem o "
            "leiaute/Nota Técnica vigente na data da emissão",
            "Treinar equipe para não misturar base antiga com base nova no "
            "mesmo fechamento sem rastreio",
            "Confirmar calendário oficial vigente (RFB / comitês) antes de "
            "tratar qualquer marco como fato fechado",
        ],
        "method_note": (
            "Confirmar calendário e leiautes oficiais vigentes. "
            "Este item não afirma datas de obrigatoriedade nem alíquotas."
        ),
    },
    {
        "id": "disclaimer_crc",
        "title": "Papel do LexScan vs. contador CRC",
        "summary": (
            "LexScan auxilia; contador CRC valida; legislação muda."
        ),
        "steps": [
            "Usar o LexScan como apoio de rotina e evidência operacional",
            "Deixar a validação final, assinatura e entrega com o contador CRC",
            "Revisitar este checklist quando houver mudança de leiaute, "
            "calendário ou orientação oficial",
        ],
        "method_note": TAX_REFORM_DISCLAIMER,
    },
]


def build_tax_reform_checklist() -> Dict[str, Any]:
    """Return static methodological checklist for API consumers."""
    return {
        "items": list(CHECKLIST_ITEMS),
        "count": len(CHECKLIST_ITEMS),
        "disclaimer": TAX_REFORM_DISCLAIMER,
        "stub": True,
        "source": "methodological_help_not_legal_advice",
    }
