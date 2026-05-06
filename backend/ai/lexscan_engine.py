"""
LexScan Engine - Processamento de Documentos Jurídicos
"""

from typing import Dict, List, Optional
from ai.groq_client import get_groq_client
from tools.ocr_processor import ocr_processor
import json

SYSTEM_PROMPT = """Você é LexScan IA, assistente jurídica especializada em análise de documentos.

INSTRUÇÕES DE FORMATAÇÃO - USE QUEBRAS DE LINHA:
**[Emoji] Título do Documento**

Contexto em 1-2 linhas.

**1. 📋 Resumo Executivo**
- Pontos principais
- Conclusão rápida

**2. ⚠️ Prazos Críticos**
- Prazo 1
- Prazo 2

**3. 👥 Partes Envolvidas**
- Autor/Réu
- Advogados

**4. 💰 Valores e Riscos**
- Valor da causa
- Riscos identificados

**💭 Recomendação Final**
Próximos passos sugeridos.

SEMPRE use quebras de linha reais entre seções.
SEJA objetiva e direta como uma advogada experiente.
Use emojis estrategicamente.
"""

class LexScanEngine:
    """Motor de processamento de documentos jurídicos"""
    
    def __init__(self):
        self.groq = get_groq_client()
        self.ocr = ocr_processor
        self.use_api = self.groq is not None and self.groq.available
        
        if self.use_api:
            print("[OK] LexScan Engine pronta! Modo: API GROQ")
        else:
            print("[AVISO] LexScan Engine sem API - usando modo básico")
    
    def process_document(self, document_text: str, document_type: str = "auto") -> Dict:
        """
        Processa documento jurídico completo
        
        Args:
            document_text: Texto extraído do documento
            document_type: Tipo de documento (auto para detectar)
            
        Returns:
            Análise completa do documento
        """
        try:
            # 1. OCR e análise básica
            ocr_data = self.ocr.analyze_document(document_text)
            
            # 2. Se tipo é auto, usar o detectado
            if document_type == "auto":
                document_type = ocr_data['document_type']
            
            # 3. Gerar análise com IA
            if self.use_api:
                analysis = self.analyze(document_text, ocr_data)
            else:
                analysis = self._generate_basic_analysis(ocr_data)
            
            return {
                'success': True,
                'document_type': document_type,
                'ocr_data': ocr_data,
                'analysis': analysis,
                'summary': ocr_data['summary'],
                'deadlines': ocr_data['deadlines'],
                'parties': ocr_data['parties'],
                'values': ocr_data['values'],
                'process_number': ocr_data['process_number'],
                'court': ocr_data['court']
            }
            
        except Exception as e:
            print(f"[ERRO] {e}")
            return {
                'success': False,
                'error': str(e),
                'document_type': 'unknown',
                'analysis': 'Erro ao processar documento.'
            }
    
    def _generate_ai_analysis(self, text: str, ocr_data: Dict) -> str:
        """Gera análise usando IA"""
        
        prompt = f"""Analise este documento jurídico e forneça uma avaliação profissional:

DADOS EXTRAÍDOS:
Tipo: {ocr_data['document_type']}
Processo: {ocr_data['process_number']}
Partes: {json.dumps(ocr_data['parties'], ensure_ascii=False)}
Prazos: {json.dumps(ocr_data['deadlines'], ensure_ascii=False)}
Valores: {json.dumps(ocr_data['values'], ensure_ascii=False)}

TEXTO DO DOCUMENTO:
{text[:3000]}

Forneça análise estruturada conforme formato indicado no system prompt.
"""
        
        try:
            response = self.groq.generate_fast(prompt, SYSTEM_PROMPT)
            return response
        except Exception as e:
            print(f"[ERRO IA] {e}")
            return self._generate_basic_analysis(ocr_data)
    
    def _generate_basic_analysis(self, ocr_data: Dict) -> str:
        """Gera análise básica quando IA não disponível"""
        
        analysis = f"""**📄 Análise do Documento**

**Tipo:** {ocr_data['document_type']}
**Processo:** {ocr_data['process_number'] or 'Não identificado'}

**1. Partes:**
- Autor: {ocr_data['parties']['autor'] or 'Não identificado'}
- Réu: {ocr_data['parties']['reu'] or 'Não identificado'}

**2. Prazos Encontrados:**
"""
        
        if ocr_data['deadlines']:
            for deadline in ocr_data['deadlines']:
                analysis += f"\n- {deadline['days']} dias: {deadline['context'][:50]}..."
        else:
            analysis += "\nNenhum prazo identificado automaticamente."
        
        analysis += "\n\n**3. Valores:**\n"
        if ocr_data['values']:
            for val in ocr_data['values'][:3]:
                analysis += f"\n- R$ {val['value']}"
        else:
            analysis += "\nNenhum valor identificado."
        
        analysis += "\n\n**💭 Recomendação:**\nVerifique prazos e valores manualmente."
        
        return analysis
    
    def chat_with_document(self, document_data: Dict, user_question: str) -> str:
        """
        Chat contextual sobre o documento
        
        Args:
            document_data: Dados do documento processado
            user_question: Pergunta do usuário
            
        Returns:
            Resposta da IA
        """
        if not self.use_api:
            return "Chat disponível apenas com API ativa."
        
        context = f"""DOCUMENTO EM ANÁLISE:
Tipo: {document_data['document_type']}
Número: {document_data.get('process_number', 'N/A')}
Partes: {json.dumps(document_data.get('parties', {}), ensure_ascii=False)}
Prazos: {json.dumps(document_data.get('deadlines', []), ensure_ascii=False)}
Resumo: {document_data.get('summary', '')[:500]}

PERGUNTA DO USUÁRIO: {user_question}

Responda como advogada especialista, de forma clara e objetiva."""
        
        try:
            return self.groq.generate_fast(context, SYSTEM_PROMPT)
        except Exception as e:
            return f"Erro ao processar pergunta: {str(e)}"
    
    def get_deadlines_calendar(self, documents: List[Dict]) -> List[Dict]:
        """
        Gera calendário de prazos de múltiplos documentos
        
        Args:
            documents: Lista de documentos processados
            
        Returns:
            Lista de prazos ordenados
        """
        all_deadlines = []
        
        for doc in documents:
            for deadline in doc.get('deadlines', []):
                all_deadlines.append({
                    'document_type': doc['document_type'],
                    'process_number': doc.get('process_number', ''),
                    'deadline': deadline,
                    'urgency': deadline.get('urgency', 'medium')
                })
        
        # Ordenar por urgência
        urgency_order = {'high': 0, 'medium': 1, 'low': 2}
        all_deadlines.sort(key=lambda x: urgency_order.get(x['urgency'], 1))
        
        return all_deadlines


# Instância global
lexscan_engine = LexScanEngine()

if __name__ == "__main__":
    # Teste
    sample = """
    Processo nº 12345-67.2024.8.26.0001
    
    Autor: Maria Souza
    Réu: Construtora XYZ Ltda
    
    Vara de Família e Sucessões
    
    Prazo para contestação: 15 dias.
    Audiência marcada para 20/04/2024.
    Valor da causa: R$ 100.000,00
    """
    
    result = lexscan_engine.process_document(sample)
    print("\n=== RESULTADO ===")
    print(f"Tipo: {result['document_type']}")
    print(f"Análise:\n{result['analysis']}")
