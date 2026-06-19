"""Structured legal and accounting document analysis engine."""

from __future__ import annotations

import json
from typing import Dict, List

from ai.groq_client import get_groq_client
from tools.ocr_processor import ocr_processor


SYSTEM_PROMPT = """Voce e a Lex, especialista em analise documental juridica e contabil.

Estruture a resposta em:
1. Resumo executivo
2. Pontos criticos e inconsistencias
3. Prazos, datas e obrigacoes
4. Partes, valores e evidencias
5. Riscos e informacoes faltantes
6. Proximos passos verificaveis

Nao invente artigo, prazo, obrigacao, valor, parte ou jurisprudencia. Diferencie
o que esta no documento do que e inferencia. Recomende revisao do advogado ou
contador responsavel antes de qualquer decisao profissional.
"""


class LexScanEngine:
    """Analyze extracted text with bounded remote context and local fallback."""

    def __init__(self):
        self.groq = get_groq_client()
        self.ocr = ocr_processor
        self.use_api = self.groq is not None and self.groq.available

    @staticmethod
    def _build_context_sample(text: str, max_characters: int = 6000) -> str:
        if len(text) <= max_characters:
            return text
        section_size = max_characters // 3
        middle_start = max((len(text) // 2) - (section_size // 2), 0)
        return (
            text[:section_size]
            + "\n\n[SECAO INTERMEDIARIA]\n\n"
            + text[middle_start : middle_start + section_size]
            + "\n\n[SECAO FINAL]\n\n"
            + text[-section_size:]
        )

    def process_document(
        self,
        document_text: str,
        document_type: str = "auto",
    ) -> Dict:
        try:
            ocr_data = self.ocr.analyze_document(document_text)
            if document_type == "auto":
                document_type = ocr_data["document_type"]

            if self.use_api:
                analysis, analysis_mode, ai_error = self._generate_ai_analysis(
                    document_text,
                    ocr_data,
                )
            else:
                analysis = self._generate_basic_analysis(ocr_data)
                analysis_mode = "local_structured"
                ai_error = ""

            return {
                "success": True,
                "document_type": document_type,
                "ocr_data": ocr_data,
                "analysis": analysis,
                "summary": ocr_data["summary"],
                "deadlines": ocr_data["deadlines"],
                "parties": ocr_data["parties"],
                "values": ocr_data["values"],
                "process_number": ocr_data["process_number"],
                "court": ocr_data["court"],
                "analysis_mode": analysis_mode,
                "ai_analysis_used": analysis_mode == "remote_ai",
                "ai_error": ai_error,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "document_type": "unknown",
                "analysis": "Erro ao processar documento.",
                "analysis_mode": "failed",
                "ai_analysis_used": False,
            }

    def _generate_ai_analysis(
        self,
        text: str,
        ocr_data: Dict,
    ) -> tuple[str, str, str]:
        context_sample = self._build_context_sample(text)
        prompt = f"""Analise o documento profissional a seguir.

DADOS EXTRAIDOS:
Tipo: {ocr_data['document_type']}
Processo: {ocr_data['process_number']}
Partes: {json.dumps(ocr_data['parties'], ensure_ascii=False)}
Prazos (amostra de ate 20): {json.dumps(ocr_data['deadlines'][:20], ensure_ascii=False)}
Valores (amostra de ate 20): {json.dumps(ocr_data['values'][:20], ensure_ascii=False)}

AMOSTRA REPRESENTATIVA DO INICIO, MEIO E FIM:
{context_sample}

Informe tambem quando a amostra nao permite concluir algo sobre o arquivo integral.
"""
        try:
            response = self.groq.generate_fast(prompt, SYSTEM_PROMPT)
            return response, "remote_ai", ""
        except Exception as exc:
            return self._generate_basic_analysis(ocr_data), "local_structured", str(exc)

    @staticmethod
    def _generate_basic_analysis(ocr_data: Dict) -> str:
        parties = ocr_data.get("parties") or {}
        deadlines = ocr_data.get("deadlines") or []
        values = ocr_data.get("values") or []
        lines = [
            "## Analise documental estruturada",
            "",
            "### Resumo executivo",
            str(ocr_data.get("summary") or "Resumo automatico indisponivel."),
            "",
            "### Identificacao",
            f"- Tipo: {ocr_data.get('document_type') or 'nao identificado'}",
            f"- Processo: {ocr_data.get('process_number') or 'nao identificado'}",
            f"- Orgao ou juizo: {ocr_data.get('court') or 'nao identificado'}",
            f"- Autor/requerente: {parties.get('autor') or 'nao identificado'}",
            f"- Reu/requerido: {parties.get('reu') or 'nao identificado'}",
            "",
            f"### Prazos e obrigacoes ({len(deadlines)} ocorrencias detectadas)",
        ]
        if deadlines:
            lines.extend(
                f"- {item.get('days', '?')} dias: {str(item.get('context') or '')[:180]}"
                for item in deadlines[:10]
            )
        else:
            lines.append("- Nenhum prazo foi identificado automaticamente.")

        lines.extend(
            [
                "",
                f"### Valores ({len(values)} ocorrencias detectadas)",
            ]
        )
        if values:
            lines.extend(
                f"- R$ {item.get('value', '?')}: {str(item.get('context') or '')[:160]}"
                for item in values[:10]
            )
        else:
            lines.append("- Nenhum valor foi identificado automaticamente.")

        lines.extend(
            [
                "",
                "### Riscos e limites",
                "- A extracao automatica pode conter repeticoes ou erros de OCR.",
                "- Prazos, valores e qualificacoes devem ser conferidos no original.",
                "- Nao foi gerada conclusao normativa sem fonte oficial vinculada.",
                "",
                "### Proximos passos",
                "- Conferir os trechos destacados no arquivo integral.",
                "- Validar datas, partes, valores e obrigacoes com os documentos de suporte.",
                "- Submeter a conclusao ao advogado ou contador responsavel.",
            ]
        )
        return "\n".join(lines)

    def chat_with_document(self, document_data: Dict, user_question: str) -> str:
        if not self.use_api:
            return "Chat contextual indisponivel sem provedor de IA."
        context = f"""DOCUMENTO:
Tipo: {document_data.get('document_type', 'N/A')}
Numero: {document_data.get('process_number', 'N/A')}
Partes: {json.dumps(document_data.get('parties', {}), ensure_ascii=False)}
Prazos: {json.dumps(document_data.get('deadlines', [])[:20], ensure_ascii=False)}
Resumo: {str(document_data.get('summary', ''))[:1000]}

PERGUNTA: {user_question}
"""
        try:
            return self.groq.generate_fast(context, SYSTEM_PROMPT)
        except Exception as exc:
            return f"Nao foi possivel processar a pergunta: {exc}"

    @staticmethod
    def get_deadlines_calendar(documents: List[Dict]) -> List[Dict]:
        all_deadlines = []
        for document in documents:
            for deadline in document.get("deadlines", []):
                all_deadlines.append(
                    {
                        "document_type": document["document_type"],
                        "process_number": document.get("process_number", ""),
                        "deadline": deadline,
                        "urgency": deadline.get("urgency", "medium"),
                    }
                )
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        all_deadlines.sort(key=lambda item: urgency_order.get(item["urgency"], 1))
        return all_deadlines


lexscan_engine = LexScanEngine()
