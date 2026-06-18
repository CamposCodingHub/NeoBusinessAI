"""
Dual Extraction com Reconciliation
==================================
Implementa dois extractores independentes e valida concordância
Baseado em referências enterprise (AWS Doczy.ai, SAP Document AI)
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Resultado de extração"""
    extractor_name: str
    data: Dict[str, Any]
    confidence: float
    processing_time_ms: int
    metadata: Dict[str, Any] = None


class SpecialistExtractor:
    """
    Extrator Especialista (LayoutLMv3, Donut)
    Focado em documentos estruturados, estável
    """
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Carrega modelo especialista"""
        try:
            # Futuro: carregar LayoutLMv3 ou Donut
            # Por enquanto, usa extração baseada em regras
            logger.info("✅ SpecialistExtractor inicializado (modo regras)")
        except Exception as e:
            logger.warning(f"Falha ao carregar modelo especialista: {e}")
    
    async def extract(self, text: str, document_type: str = "general") -> ExtractionResult:
        """
        Extrai dados usando modelo especialista
        """
        start_time = datetime.utcnow()
        
        # Extração baseada em regras (placeholder)
        data = {
            "deadlines": self._extract_deadlines(text),
            "values": self._extract_values(text),
            "parties": self._extract_parties(text),
            "dates": self._extract_dates(text)
        }
        
        confidence = 0.85  # Alta confiança para documentos estruturados
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ExtractionResult(
            extractor_name="specialist",
            data=data,
            confidence=confidence,
            processing_time_ms=int(processing_time),
            metadata={"model": "rules_based", "document_type": document_type}
        )
    
    def _extract_deadlines(self, text: str) -> List[Dict]:
        """Extrai prazos"""
        import re
        deadlines = []
        
        # Padrões de prazo
        patterns = [
            r'prazo de (\d+) dias',
            r'data limite: (\d{2}/\d{2}/\d{4})',
            r'vence em (\d{2}/\d{2}/\d{4})'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                deadlines.append({
                    "text": match.group(0),
                    "type": "deadline"
                })
        
        return deadlines
    
    def _extract_values(self, text: str) -> List[Dict]:
        """Extrai valores monetários"""
        import re
        values = []
        
        pattern = r'R\$\s*[\d.,]+'
        matches = re.finditer(pattern, text)
        for match in matches:
            values.append({
                "text": match.group(0),
                "type": "monetary"
            })
        
        return values
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extrai partes (autor, réu)"""
        parties = []
        
        keywords = ['autor', 'réu', 'requerente', 'requerido']
        for keyword in keywords:
            if keyword.lower() in text.lower():
                parties.append(keyword)
        
        return parties
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extrai datas"""
        import re
        pattern = r'\d{1,2}/\d{1,2}/\d{4}'
        return re.findall(pattern, text)


class VisionLanguageModelExtractor:
    """
    Extrator VLM (Claude 3.5, Qwen2.5-VL)
    Robusto a variações de layout, menos estável
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Carrega modelo VLM"""
        try:
            # Futuro: carregar Claude 3.5 Vision ou Qwen2.5-VL
            # Por enquanto, usa Groq como fallback
            logger.info("✅ VLMExtractor inicializado (modo Groq)")
        except Exception as e:
            logger.warning(f"Falha ao carregar modelo VLM: {e}")
    
    async def extract(self, text: str, image: Optional[bytes] = None) -> ExtractionResult:
        """
        Extrai dados usando VLM
        """
        start_time = datetime.utcnow()
        
        # Extração usando Groq (placeholder para VLM real)
        data = {
            "deadlines": self._extract_with_llm(text),
            "values": self._extract_with_llm(text),
            "parties": self._extract_with_llm(text),
            "dates": self._extract_with_llm(text),
            "summary": self._generate_summary(text)
        }
        
        confidence = 0.75  # Média confiança para VLM
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ExtractionResult(
            extractor_name="vlm",
            data=data,
            confidence=confidence,
            processing_time_ms=int(processing_time),
            metadata={"model": "groq_llm", "has_image": image is not None}
        )
    
    def _extract_with_llm(self, text: str) -> List[str]:
        """Extrai usando LLM"""
        # Placeholder - usaria Groq API aqui
        return []
    
    def _generate_summary(self, text: str) -> str:
        """Gera resumo usando LLM"""
        # Placeholder
        return text[:200] + "..." if len(text) > 200 else text


class ReconciliationEngine:
    """
    Motor de Reconciliação
    Compara resultados de múltiplos extractors e valida concordância
    """
    
    def __init__(self):
        self.confidence_thresholds = {
            "auto_approve": 0.95,
            "spot_check": 0.85,
            "full_review": 0.0
        }
    
    def reconcile(
        self,
        results: List[ExtractionResult]
    ) -> Dict[str, Any]:
        """
        Reconcilia resultados de múltiplos extractors
        """
        if len(results) < 2:
            return {
                "status": "single_source",
                "data": results[0].data if results else {},
                "confidence": results[0].confidence if results else 0.0,
                "recommendation": "use_single"
            }
        
        # Comparar resultados
        comparison = self._compare_results(results)
        
        # Determinar ação baseada em concordância
        if comparison["agreement"] >= self.confidence_thresholds["auto_approve"]:
            return {
                "status": "auto_approved",
                "data": self._merge_results(results),
                "confidence": comparison["avg_confidence"],
                "recommendation": "auto_approve",
                "comparison": comparison
            }
        elif comparison["agreement"] >= self.confidence_thresholds["spot_check"]:
            return {
                "status": "spot_check",
                "data": self._merge_results(results),
                "confidence": comparison["avg_confidence"],
                "recommendation": "spot_check_audit",
                "comparison": comparison,
                "discrepancies": comparison["discrepancies"]
            }
        else:
            return {
                "status": "full_review",
                "data": self._merge_results(results),
                "confidence": comparison["avg_confidence"],
                "recommendation": "human_review",
                "comparison": comparison,
                "discrepancies": comparison["discrepancies"],
                "explanation": self._generate_explanation(comparison)
            }
    
    def _compare_results(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """Compara resultados dos extractors"""
        comparison = {
            "agreement": 0.0,
            "avg_confidence": 0.0,
            "discrepancies": [],
            "field_agreement": {}
        }
        
        # Calcular confiança média
        comparison["avg_confidence"] = sum(r.confidence for r in results) / len(results)
        
        # Comparar campo por campo
        if len(results) >= 2:
            # Comparar deadlines
            deadlines_0 = set(d.get("text", "") for d in results[0].data.get("deadlines", []))
            deadlines_1 = set(d.get("text", "") for d in results[1].data.get("deadlines", []))
            
            if deadlines_0 and deadlines_1:
                overlap = len(deadlines_0 & deadlines_1) / max(len(deadlines_0), len(deadlines_1))
                comparison["field_agreement"]["deadlines"] = overlap
            else:
                comparison["field_agreement"]["deadlines"] = 1.0  # Ambos vazios
            
            # Calcular concordância geral
            field_agreements = comparison["field_agreement"].values()
            comparison["agreement"] = sum(field_agreements) / len(field_agreements) if field_agreements else 0.0
            
            # Identificar discrepâncias
            if comparison["agreement"] < 0.8:
                if comparison["field_agreement"].get("deadlines", 1.0) < 0.8:
                    comparison["discrepancies"].append("deadlines")
        
        return comparison
    
    def _merge_results(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """Merge de resultados de múltiplos extractors"""
        merged = {
            "deadlines": [],
            "values": [],
            "parties": [],
            "dates": [],
            "summary": ""
        }
        
        for result in results:
            for key in merged.keys():
                if key in result.data:
                    if isinstance(result.data[key], list):
                        merged[key].extend(result.data[key])
                    else:
                        merged[key] = result.data[key]
        
        # Remover duplicatas
        for key in ["deadlines", "values", "parties", "dates"]:
            if isinstance(merged[key], list):
                merged[key] = list(set(merged[key]))
        
        return merged
    
    def _generate_explanation(self, comparison: Dict) -> str:
        """Gera explicação para revisão humana"""
        explanations = []
        
        if "deadlines" in comparison.get("discrepancies", []):
            explanations.append("Os extractores discordam sobre os prazos identificados.")
        
        if comparison["avg_confidence"] < 0.7:
            explanations.append("A confiança média dos extractors é baixa.")
        
        if not explanations:
            explanations.append("Baixa concordância geral entre extractors.")
        
        return " ".join(explanations)


class DualExtractionPipeline:
    """
    Pipeline de Dual Extraction
    Executa dois extractores independentes e reconcilia resultados
    """
    
    def __init__(self, vlm_api_key: Optional[str] = None):
        self.specialist = SpecialistExtractor()
        self.vlm = VisionLanguageModelExtractor(vlm_api_key)
        self.reconciliation = ReconciliationEngine()
    
    async def extract(
        self,
        text: str,
        image: Optional[bytes] = None,
        document_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Executa dual extraction completa
        """
        logger.info(f"[DUAL EXTRACTION] Iniciando extração para documento tipo: {document_type}")
        
        # Executar extractores em paralelo
        results = await asyncio.gather(
            self.specialist.extract(text, document_type),
            self.vlm.extract(text, image)
        )
        
        # Reconciliar resultados
        reconciliation = self.reconciliation.reconcile(results)
        
        logger.info(f"[DUAL EXTRACTION] Status: {reconciliation['status']}")
        
        return {
            "extraction_results": [
                {
                    "extractor": r.extractor_name,
                    "confidence": r.confidence,
                    "processing_time_ms": r.processing_time_ms
                }
                for r in results
            ],
            "reconciliation": reconciliation,
            "final_data": reconciliation["data"],
            "recommendation": reconciliation["recommendation"],
            "total_processing_time_ms": sum(r.processing_time_ms for r in results)
        }


# Instância global
from config import settings

dual_extraction_pipeline = DualExtractionPipeline(
    vlm_api_key=os.getenv("ANTHROPIC_API_KEY")  # Para Claude Vision
)
