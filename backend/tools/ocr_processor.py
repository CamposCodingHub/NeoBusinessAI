"""
OCR Processor - LexScan IA
Processamento de documentos jurídicos com OCR
"""

import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytesseract
from PIL import Image
import io

class OCRProcessor:
    """Processa documentos jurídicos com OCR"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        self.max_extracted_items = 100
        
    def extract_text(self, image_data: bytes) -> str:
        """
        Extrai texto de imagem usando OCR
        
        Args:
            image_data: Bytes da imagem
            
        Returns:
            Texto extraído
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Configurações para português e melhor precisão
            config = '--oem 3 --psm 6 -l por+eng'
            
            text = pytesseract.image_to_string(image, config=config)
            
            return text.strip()
            
        except Exception as e:
            print(f"[OCR ERROR] {e}")
            return ""
    
    def analyze_document(self, text: str) -> Dict:
        """
        Analisa documento jurídico e extrai informações
        
        Args:
            text: Texto do documento
            
        Returns:
            Dicionário com informações extraídas
        """
        return {
            'summary': self._generate_summary(text),
            'deadlines': self._extract_deadlines(text),
            'parties': self._extract_parties(text),
            'document_type': self._classify_document(text),
            'values': self._extract_values(text),
            'process_number': self._extract_process_number(text),
            'court': self._extract_court(text)
        }
    
    def _generate_summary(self, text: str) -> str:
        """Gera resumo do documento"""
        # Primeiras 500 caracteres como resumo inicial
        # IA vai melhorar isso depois
        return text[:500] + "..." if len(text) > 500 else text
    
    def _extract_deadlines(self, text: str) -> List[Dict]:
        """Extrai prazos do documento"""
        deadlines = []
        
        # Padrões de prazos em português
        prazo_patterns = [
            r'(\d+)\s*dias?\s*(?:úteis?)?\s*(?:para|a partir de|contados?|às?)',
            r'prazo\s*(?:de)?\s*(\d+)\s*dias?',
            r'(?:intimar|notificar|cit[oa]r)\s*.*?(\d+)\s*dias?',
            r'(?:resposta|defesa|recurso)\s*.*?(\d+)\s*dias?',
            r'(?:audi[êe]ncia|sess[ãa]o|julga[çc]amento)\s*.*?data\s*:?\s*(\d{2}/\d{2}/\d{4})',
        ]
        
        # Padrões de datas
        date_patterns = [
            r'(\d{2}/\d{2}/\d{4})',
            r'(\d{2}-\d{2}-\d{4})',
            r'(\d{2}\.\d{2}\.\d{4})',
        ]
        
        text_lower = text.lower()
        
        # Procura por prazos
        for pattern in prazo_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                days = match.group(1) if match.groups() else "15"
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end]
                
                deadlines.append({
                    'type': 'prazo',
                    'days': days,
                    'context': context.strip(),
                    'urgency': 'high' if int(days) <= 5 else 'medium' if int(days) <= 15 else 'low'
                })
                if len(deadlines) >= self.max_extracted_items:
                    return deadlines
        
        return deadlines
    
    def _extract_parties(self, text: str) -> Dict:
        """Extrai partes do processo"""
        parties = {
            'autor': '',
            'reu': '',
            'advogados': []
        }
        
        # Padrões para partes
        autor_patterns = [
            r'autor[es]?\s*:?\s*([A-Z][A-Za-z\s]+?)(?=\n|reu|denunciado|advogado)',
            r'requerente\s*:?\s*([A-Z][A-Za-z\s]+?)(?=\n|requerido)',
        ]
        
        reu_patterns = [
            r'reu[s]?\s*:?\s*([A-Z][A-Za-z\s]+?)(?=\n|autor|denunciante|advogado)',
            r'requerido[s]?\s*:?\s*([A-Z][A-Za-z\s]+?)(?=\n|requerente)',
            r'denunciado[s]?\s*:?\s*([A-Z][A-Za-z\s]+?)(?=\n|denunciante)',
        ]
        
        adv_patterns = [
            r'advogado[s]?\s*:?\s*([A-Z][A-Za-z\s]+?)(?=\n|\d|OAB)',
            r'OAB[/\s]?[A-Z]+\s*\d+',  # Número OAB
        ]
        
        # Extrair autor
        for pattern in autor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parties['autor'] = match.group(1).strip()
                break
        
        # Extrair réu
        for pattern in reu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parties['reu'] = match.group(1).strip()
                break
        
        # Extrair advogados
        for pattern in adv_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                parties['advogados'].append(match.group(0).strip())
                if len(parties['advogados']) >= self.max_extracted_items:
                    break
        
        return parties
    
    def _classify_document(self, text: str) -> str:
        """Classifica tipo de documento jurídico"""
        text_lower = text.lower()
        
        keywords = {
            'peticao_inicial': ['petição inicial', 'demanda', 'requerimento', 'pedido'],
            'contestacao': ['contestação', 'resposta', 'defesa', 'alegações'],
            'recurso': ['recurso', 'apelação', 'agravo', 'especial', 'extraordinário'],
            'sentenca': ['sentença', 'decisão', 'julgamento', 'acórdão'],
            'despacho': ['despacho', 'decisão interlocutória', 'determino'],
            'mandado': ['mandado de segurança', 'mandado segurança', 'liminar'],
            'execucao': ['execução', 'penhora', 'satisfação'],
            'notificacao': ['notificação', 'intimação', 'citação'],
            'contrato': ['contrato', 'acordo', 'transação', 'convênio'],
            'procuracao': ['procuração', 'procuração ad judicia', 'outorga'],
        }
        
        for doc_type, words in keywords.items():
            if any(word in text_lower for word in words):
                return doc_type
        
        return 'documento_generico'
    
    def _extract_values(self, text: str) -> List[Dict]:
        """Extrai valores monetários"""
        values = []
        
        # Padrões de valores
        value_patterns = [
            r'R\$\s*([\d.,]+(?:\.\d{2})?)',
            r'(\d+[.,]\d{2})\s*(?:reais?)',
            r'valor\s*(?:de)?\s*R?\$?\s*([\d.,]+)',
            r'dano\s*material.*?([\d.,]+)',
            r'indenização.*?([\d.,]+)',
        ]
        
        for pattern in value_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1) if match.groups() else match.group(0)
                context_start = max(0, match.start() - 30)
                context_end = min(len(text), match.end() + 30)
                
                values.append({
                    'value': value_str,
                    'context': text[context_start:context_end].strip()
                })
                if len(values) >= self.max_extracted_items:
                    return values
        
        return values
    
    def _extract_process_number(self, text: str) -> str:
        """Extrai número do processo"""
        # Padrão CNJ: NNNNNNN-NN.NNNN.N.NN.NNNN
        pattern = r'\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}'
        match = re.search(pattern, text)
        
        if match:
            return match.group(0)
        
        # Padrões alternativos
        alt_patterns = [
            r'processo\s*n[º°]?\s*(\d[-\d./]+)',
            r'n[º°]\s*(\d{4,}[-\d./]*)',
        ]
        
        for pattern in alt_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ''
    
    def _extract_court(self, text: str) -> str:
        """Extrai vara/tribunal"""
        text_lower = text.lower()
        
        court_keywords = [
            'vara', 'tribunal', 'fórum', 'comarca', 'juízo',
            'trf', 'tj', 'stf', 'stj', 'justiça federal',
            'trabalhista', 'criminal', 'cível', 'família',
            'fazenda pública', 'execuções', 'registros'
        ]
        
        for keyword in court_keywords:
            if keyword in text_lower:
                # Extrai contexto
                idx = text_lower.find(keyword)
                context_start = max(0, idx - 30)
                context_end = min(len(text), idx + 50)
                return text[context_start:context_end].strip()
        
        return ''


# Instância global
ocr_processor = OCRProcessor()

if __name__ == "__main__":
    # Teste
    sample_text = """
    PROCESSO Nº 0001234-56.2024.8.26.0100
    
    AUTOR: João Silva
    ADVOGADO: Dr. Carlos Mendes OAB/SP 123456
    
    RÉU: Empresa ABC Ltda
    
    Vara da Justiça Civil de São Paulo
    
    Intime-se o réu para apresentar resposta em 15 dias.
    
    Valor da causa: R$ 50.000,00
    
    Audiência de conciliação marcada para 15/03/2024 às 14:00h.
    """
    
    processor = OCRProcessor()
    result = processor.analyze_document(sample_text)
    
    print("Tipo:", result['document_type'])
    print("Processo:", result['process_number'])
    print("Partes:", result['parties'])
    print("Prazos:", result['deadlines'])
    print("Valores:", result['values'])
