"""
Operations Intelligence Service
===============================
Gera uma leitura operacional consolidada do escritorio para dashboards,
copilotos, simulacoes e priorizacao de melhoria.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from database import Client, Deadline, Document, Invoice, LegalDocument, WhatsAppConfig


class OperationsIntelligenceService:
    """Camada de inteligencia operacional baseada em regras."""

    def build_overview(self, db: Session, user_id: int) -> Dict[str, Any]:
        now = datetime.utcnow()
        soon = now + timedelta(days=7)

        documents = db.query(Document).filter(Document.user_id == user_id).all()
        deadlines = db.query(Deadline).filter(Deadline.user_id == user_id).all()
        clients = db.query(Client).filter(Client.user_id == user_id).all()
        invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
        legal_pieces = db.query(LegalDocument).filter(LegalDocument.user_id == user_id).all()
        whatsapp_config = (
            db.query(WhatsAppConfig).filter(WhatsAppConfig.user_id == user_id).first()
        )

        uploaded_docs = [doc for doc in documents if doc.status == "uploaded"]
        processing_docs = [doc for doc in documents if doc.status == "processing"]
        completed_docs = [doc for doc in documents if doc.status in {"completed", "processed"}]

        pending_deadlines = [dl for dl in deadlines if not dl.is_completed]
        overdue_deadlines = [
            dl for dl in pending_deadlines if dl.due_date and dl.due_date < now
        ]
        urgent_deadlines = [
            dl for dl in pending_deadlines if dl.due_date and dl.due_date <= soon
        ]

        active_clients = [client for client in clients if client.status == "active"]
        lead_clients = [client for client in clients if client.status == "prospect"]
        inactive_clients = [client for client in clients if client.status == "inactive"]

        paid_invoices = [inv for inv in invoices if inv.status == "paid"]
        pending_invoices = [inv for inv in invoices if inv.status == "pending"]
        overdue_invoices = [inv for inv in invoices if inv.status == "overdue"]
        open_invoices = [inv for inv in invoices if inv.status in {"pending", "overdue"}]

        draft_pieces = [piece for piece in legal_pieces if piece.status == "generating"]
        ready_pieces = [piece for piece in legal_pieces if piece.status == "completed"]

        financial = {
            "paid_total": round(sum(inv.total_cents for inv in paid_invoices) / 100, 2),
            "pending_total": round(sum(inv.total_cents for inv in pending_invoices) / 100, 2),
            "overdue_total": round(sum(inv.total_cents for inv in overdue_invoices) / 100, 2),
            "open_total": round(sum(inv.total_cents for inv in open_invoices) / 100, 2),
        }

        automation = {
            "whatsapp_connected": bool(
                whatsapp_config and whatsapp_config.is_active and whatsapp_config.is_connected
            ),
            "auto_notify_deadlines": bool(
                whatsapp_config and whatsapp_config.auto_notify_deadlines
            ),
            "auto_notify_invoices": bool(
                whatsapp_config and whatsapp_config.auto_notify_invoices
            ),
        }

        maturity = {
            "document_ops": self._score_document_ops(documents, uploaded_docs, processing_docs),
            "deadline_ops": self._score_deadline_ops(pending_deadlines, overdue_deadlines),
            "client_ops": self._score_client_ops(active_clients, lead_clients, inactive_clients),
            "financial_ops": self._score_financial_ops(financial, invoices),
            "automation_ops": self._score_automation_ops(automation),
        }
        overall_score = round(sum(maturity.values()) / len(maturity), 1)

        recommendations = self._build_recommendations(
            uploaded_docs=uploaded_docs,
            processing_docs=processing_docs,
            overdue_deadlines=overdue_deadlines,
            urgent_deadlines=urgent_deadlines,
            lead_clients=lead_clients,
            overdue_invoices=overdue_invoices,
            pending_invoices=pending_invoices,
            automation=automation,
            draft_pieces=draft_pieces,
        )

        overview = {
            "generated_at": now.isoformat(),
            "workspace": {
                "documents": {
                    "total": len(documents),
                    "uploaded": len(uploaded_docs),
                    "processing": len(processing_docs),
                    "completed": len(completed_docs),
                },
                "deadlines": {
                    "total": len(deadlines),
                    "pending": len(pending_deadlines),
                    "overdue": len(overdue_deadlines),
                    "due_next_7_days": len(urgent_deadlines),
                },
                "clients": {
                    "total": len(clients),
                    "active": len(active_clients),
                    "prospects": len(lead_clients),
                    "inactive": len(inactive_clients),
                },
                "finance": financial,
                "legal_pieces": {
                    "total": len(legal_pieces),
                    "draft_like": len(draft_pieces),
                    "ready": len(ready_pieces),
                },
                "automation": automation,
            },
            "maturity_score": overall_score,
            "maturity_breakdown": maturity,
            "recommendations": recommendations,
            "next_best_actions": [item["title"] for item in recommendations[:5]],
            "executive_summary": self._build_executive_summary(
                overall_score=overall_score,
                overdue_deadlines=len(overdue_deadlines),
                overdue_invoices=len(overdue_invoices),
                lead_clients=len(lead_clients),
                automation=automation,
            ),
        }

        return overview

    def build_markdown_summary(self, overview: Dict[str, Any]) -> str:
        workspace = overview["workspace"]
        recommendations = overview["recommendations"][:5]

        lines = [
            "# Resumo Operacional",
            "",
            f"- Score de maturidade: **{overview['maturity_score']} / 100**",
            f"- Documentos: **{workspace['documents']['total']}** totais, **{workspace['documents']['completed']}** concluidos",
            f"- Prazos: **{workspace['deadlines']['pending']}** pendentes, **{workspace['deadlines']['overdue']}** atrasados",
            f"- Clientes: **{workspace['clients']['active']}** ativos, **{workspace['clients']['prospects']}** prospects",
            f"- Financeiro aberto: **R$ {workspace['finance']['open_total']:.2f}**",
            f"- WhatsApp conectado: **{'sim' if workspace['automation']['whatsapp_connected'] else 'nao'}**",
            "",
            "## Recomendacoes prioritarias",
        ]

        if recommendations:
            for item in recommendations:
                lines.append(
                    f"- [{item['priority'].upper()}] {item['title']}: {item['description']}"
                )
        else:
            lines.append("- Nenhuma acao critica detectada no momento.")

        lines.extend(["", "## Leitura executiva", overview["executive_summary"]])
        return "\n".join(lines)

    def _score_document_ops(
        self,
        documents: List[Document],
        uploaded_docs: List[Document],
        processing_docs: List[Document],
    ) -> float:
        if not documents:
            return 35.0
        score = 85.0 - len(uploaded_docs) * 8 - len(processing_docs) * 4
        return max(0.0, min(100.0, score))

    def _score_deadline_ops(
        self, pending_deadlines: List[Deadline], overdue_deadlines: List[Deadline]
    ) -> float:
        if not pending_deadlines and not overdue_deadlines:
            return 92.0
        score = 88.0 - len(overdue_deadlines) * 18
        score -= max(0, len(pending_deadlines) - len(overdue_deadlines)) * 2
        return max(0.0, min(100.0, score))

    def _score_client_ops(
        self,
        active_clients: List[Client],
        lead_clients: List[Client],
        inactive_clients: List[Client],
    ) -> float:
        score = 65.0
        if active_clients:
            score += 15.0
        if lead_clients:
            score += min(10.0, len(lead_clients) * 2.0)
        if inactive_clients:
            score -= min(15.0, len(inactive_clients) * 2.0)
        return max(0.0, min(100.0, score))

    def _score_financial_ops(self, financial: Dict[str, float], invoices: List[Invoice]) -> float:
        if not invoices:
            return 45.0
        score = 82.0
        open_total = financial["open_total"]
        overdue_total = financial["overdue_total"]
        if open_total > 0:
            score -= round((overdue_total / open_total) * 40, 1)
        return max(0.0, min(100.0, score))

    def _score_automation_ops(self, automation: Dict[str, bool]) -> float:
        score = 30.0
        if automation["whatsapp_connected"]:
            score += 35.0
        if automation["auto_notify_deadlines"]:
            score += 20.0
        if automation["auto_notify_invoices"]:
            score += 15.0
        return max(0.0, min(100.0, score))

    def _build_recommendations(
        self,
        *,
        uploaded_docs: List[Document],
        processing_docs: List[Document],
        overdue_deadlines: List[Deadline],
        urgent_deadlines: List[Deadline],
        lead_clients: List[Client],
        overdue_invoices: List[Invoice],
        pending_invoices: List[Invoice],
        automation: Dict[str, bool],
        draft_pieces: List[LegalDocument],
    ) -> List[Dict[str, Any]]:
        recommendations: List[Dict[str, Any]] = []

        if overdue_deadlines:
            recommendations.append(
                {
                    "priority": "critical",
                    "module": "deadlines",
                    "title": "Zerar prazos atrasados",
                    "description": f"Existem {len(overdue_deadlines)} prazos atrasados exigindo acao imediata.",
                    "expected_impact": "reduzir risco processual e retrabalho",
                }
            )

        if overdue_invoices:
            recommendations.append(
                {
                    "priority": "critical",
                    "module": "finance",
                    "title": "Ativar regua de cobranca sobre inadimplentes",
                    "description": f"{len(overdue_invoices)} faturas estao atrasadas e impactam o caixa.",
                    "expected_impact": "recuperar receita e melhorar previsao financeira",
                }
            )

        if uploaded_docs:
            recommendations.append(
                {
                    "priority": "high",
                    "module": "documents",
                    "title": "Processar backlog documental",
                    "description": f"{len(uploaded_docs)} documentos ainda nao viraram prazo, resumo nem acao.",
                    "expected_impact": "acelerar intake e reduzir trabalho manual",
                }
            )

        if urgent_deadlines and not automation["auto_notify_deadlines"]:
            recommendations.append(
                {
                    "priority": "high",
                    "module": "whatsapp",
                    "title": "Ligar notificacoes automaticas de prazo",
                    "description": "O escritorio ja tem prazos proximos e ainda nao automatizou avisos.",
                    "expected_impact": "reduzir esquecimentos e melhorar experiencia do cliente",
                }
            )

        if pending_invoices and not automation["auto_notify_invoices"]:
            recommendations.append(
                {
                    "priority": "high",
                    "module": "whatsapp",
                    "title": "Automatizar lembretes de cobranca",
                    "description": "Existem faturas pendentes sem automacao de follow-up.",
                    "expected_impact": "diminuir inadimplencia e tempo administrativo",
                }
            )

        if lead_clients:
            recommendations.append(
                {
                    "priority": "medium",
                    "module": "clients",
                    "title": "Converter prospects em clientes ativos",
                    "description": f"{len(lead_clients)} oportunidades ainda nao entraram no fluxo operacional.",
                    "expected_impact": "aumentar receita e ocupacao da equipe",
                }
            )

        if processing_docs:
            recommendations.append(
                {
                    "priority": "medium",
                    "module": "documents",
                    "title": "Revisar documentos em processamento",
                    "description": f"{len(processing_docs)} documentos ainda aguardam fechamento do pipeline.",
                    "expected_impact": "garantir consistencia do funil documental",
                }
            )

        if draft_pieces:
            recommendations.append(
                {
                    "priority": "medium",
                    "module": "legal",
                    "title": "Fechar rascunhos de pecas",
                    "description": f"{len(draft_pieces)} pecas ainda aguardam revisao humana.",
                    "expected_impact": "diminuir tempo ate protocolo ou envio",
                }
            )

        if not automation["whatsapp_connected"]:
            recommendations.append(
                {
                    "priority": "medium",
                    "module": "whatsapp",
                    "title": "Conectar canal WhatsApp",
                    "description": "O principal diferencial operacional do produto ainda esta desligado.",
                    "expected_impact": "fortalecer portal, cobranca e comunicacao",
                }
            )

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda item: priority_order.get(item["priority"], 9))
        return recommendations

    def _build_executive_summary(
        self,
        *,
        overall_score: float,
        overdue_deadlines: int,
        overdue_invoices: int,
        lead_clients: int,
        automation: Dict[str, bool],
    ) -> str:
        summary = [f"O escritorio opera hoje com score de maturidade {overall_score}/100."]

        if overdue_deadlines:
            summary.append(
                f"A principal prioridade imediata e conter {overdue_deadlines} prazos atrasados."
            )
        elif overdue_invoices:
            summary.append(
                f"O maior gargalo atual esta no financeiro, com {overdue_invoices} cobrancas vencidas."
            )
        else:
            summary.append(
                "Nao ha gargalos criticos evidentes entre prazo e cobranca neste recorte."
            )

        if lead_clients:
            summary.append(
                f"Ha {lead_clients} oportunidades comerciais prontas para nutricao ou conversao."
            )

        if not automation["whatsapp_connected"]:
            summary.append(
                "A automacao omnicanal ainda nao esta ativada, o que reduz o potencial de diferenciacao do produto."
            )
        else:
            summary.append(
                "A camada de automacao ja pode ser usada para transformar operacao em vantagem competitiva."
            )

        return " ".join(summary)


operations_intelligence_service = OperationsIntelligenceService()
