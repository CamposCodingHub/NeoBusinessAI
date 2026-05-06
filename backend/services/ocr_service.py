"""
OCR Service
============
Serviço de OCR com Tesseract para extração de texto de documentos.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import io
import re

from core.config import settings
from models.document import Document, DocumentStatus
from models.audit_log import AuditLog, AuditAction, AuditSeverity


class OCRService:
    """Serviço de OCR para extração de texto"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    
    async def process_document(
        self,
        db: Session,
        document: Document,
        file_content: bytes
    ) -> Dict[str, Any]:
        """
        Processa documento com OCR.
        
        Args:
            db: Sessão do banco
            document: Documento a processar
            file_content: Conteúdo do arquivo
            
        Returns:
            Dict com resultado do OCR
        """
        try:
            # Atualizar status
            document.status = DocumentStatus.PROCESSING
            db.commit()
            
            # Verificar formato
            if document.file_type not in self.supported_formats:
                raise ValueError(f"Formato não suportado: {document.file_type}")
            
            # Extrair texto
            if document.file_type == '.pdf':
                text, confidence = await self._process_pdf(file_content)
            else:
                text, confidence = await self._process_image(file_content)
            
            # Extrair entidades e dados
            entities = self._extract_entities(text)
            key_points = self._extract_key_points(text)
            
            # Atualizar documento
            document.ocr_text = text
            document.ocr_confidence = confidence
            document.status = DocumentStatus.PROCESSED
            document.processed_at = datetime.utcnow()
            document.entities = entities
            document.key_points = key_points
            
            # Gerar resumo com IA
            summary = await self._generate_summary(text)
            document.summary = summary
            
            db.commit()
            
            # Log de auditoria
            AuditLog.create(
                tenant_id=document.tenant_id,
                user_id=document.user_id,
                action=AuditAction.DOCUMENT_UPLOAD,
                severity=AuditSeverity.INFO,
                description="Document processed with OCR",
                metadata={
                    "document_id": str(document.id),
                    "file_type": document.file_type,
                    "confidence": confidence,
                    "text_length": len(text)
                }
            )
            
            return {
                "success": True,
                "text": text,
                "confidence": confidence,
                "entities": entities,
                "key_points": key_points,
                "summary": summary
            }
            
        except Exception as e:
            # Log erro
            document.status = DocumentStatus.ERROR
            document.error_message = str(e)
            db.commit()
            
            AuditLog.create(
                tenant_id=document.tenant_id,
                user_id=document.user_id,
                action=AuditAction.SECURITY_ALERT,
                severity=AuditSeverity.ERROR,
                description=f"OCR processing error: {str(e)}",
                metadata={"document_id": str(document.id), "error": str(e)}
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro no processamento OCR: {str(e)}"
            )
    
    async def _process_pdf(self, file_content: bytes) -> Tuple[str, int]:
        """
        Processa PDF com OCR.
        
        Args:
            file_content: Conteúdo do PDF
            
        Returns:
            Tuple[texto_extraído, confiança]
        """
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            from PIL import Image
            
            # Converter PDF para imagens
            images = convert_from_bytes(file_content, dpi=300)
            
            full_text = []
            total_confidence = 0
            
            for image in images:
                # OCR na imagem
                text = pytesseract.image_to_string(
                    image,
                    lang='por+eng',  # Português + Inglês
                    config='--psm 6'  # Assume bloco uniforme de texto
                )
                
                # Obter confiança
                data = pytesseract.image_to_data(
                    image,
                    lang='por+eng',
                    output_type=pytesseract.Output.DICT
                )
                
                confidences = [int(c) for c in data['conf'] if int(c) > 0]
                page_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                full_text.append(text)
                total_confidence += page_confidence
            
            # Calcular confiança média
            avg_confidence = int(total_confidence / len(images)) if images else 0
            
            return '\n\n'.join(full_text), avg_confidence
            
        except ImportError:
            # Fallback se Tesseract não instalado
            print("Tesseract não instalado. Usando fallback.")
            return self._fallback_pdf_text(file_content)
    
    async def _process_image(self, file_content: bytes) -> Tuple[str, int]:
        """
        Processa imagem com OCR.
        
        Args:
            file_content: Conteúdo da imagem
            
        Returns:
            Tuple[texto_extraído, confiança]
        """
        try:
            from PIL import Image
            import pytesseract
            import io
            
            # Carregar imagem
            image = Image.open(io.BytesIO(file_content))
            
            # Converter para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # OCR
            text = pytesseract.image_to_string(
                image,
                lang='por+eng',
                config='--psm 6'
            )
            
            # Obter confiança
            data = pytesseract.image_to_data(
                image,
                lang='por+eng',
                output_type=pytesseract.Output.DICT
            )
            
            confidences = [int(c) for c in data['conf'] if int(c) > 0]
            confidence = int(sum(confidences) / len(confidences)) if confidences else 0
            
            return text, confidence
            
        except ImportError:
            print("Tesseract não instalado. Usando fallback.")
            return "[OCR requer Tesseract. Instale: pip install pytesseract pdf2image pillow]", 0
    
    def _extract_entities(self, text: str) -> list:
        """
        Extrai entidades do texto (nomes, datas, valores, etc).
        
        Args:
            text: Texto extraído
            
        Returns:
            Lista de entidades
        """
        entities = []
        
        # Detectar CPF/CNPJ
        cpf_pattern = r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}'
        cnpj_pattern = r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}'
        
        cpfs = re.findall(cpf_pattern, text)
        cnpjs = re.findall(cnpj_pattern, text)
        
        for cpf in cpfs:
            entities.append({"type": "CPF", "value": cpf})
        
        for cnpj in cnpjs:
            entities.append({"type": "CNPJ", "value": cnpj})
        
        # Detectar datas
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        dates = re.findall(date_pattern, text)
        
        for date in dates[:10]:  # Limitar a 10 datas
            entities.append({"type": "DATA", "value": date})
        
        # Detectar valores monetários
        value_pattern = r'R\$\s*[\d.,]+'
        values = re.findall(value_pattern, text)
        
        for value in values[:10]:
            entities.append({"type": "VALOR", "value": value})
        
        # Detectar emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        for email in emails[:5]:
            entities.append({"type": "EMAIL", "value": email})
        
        return entities
    
    def _extract_key_points(self, text: str) -> list:
        """
        Extrai pontos-chave do texto.
        
        Args:
            text: Texto extraído
            
        Returns:
            Lista de pontos-chave
        """
        key_points = []
        
        # Dividir em parágrafos
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Pegar primeiros parágrafos como pontos-chave
        for para in paragraphs[:5]:
            if len(para) > 50:  # Ignorar parágrafos muito curtos
                key_points.append(para[:200] + "..." if len(para) > 200 else para)
        
        return key_points
    
    async def _generate_summary(self, text: str) -> str:
        """
        Gera resumo do documento com IA.
        
        Args:
            text: Texto extraído
            
        Returns:
            Resumo gerado
        """
        # Limitar texto para resumo
        max_length = 4000
        truncated_text = text[:max_length]
        
        prompt = f"""Resuma o seguinte documento jurídico em 3-5 frases principais:

{truncated_text}

Resumo:"""
        
        # TODO: Chamar IA para gerar resumo
        # Por enquanto, retorna primeira parte do texto
        sentences = text.split('.')[:3]
        return '. '.join(sentences) + '.' if sentences else "Documento processado."
    
    def _fallback_pdf_text(self, file_content: bytes) -> Tuple[str, int]:
        """
        Fallback para extração de texto de PDF quando Tesseract não disponível.
        
        Args:
            file_content: Conteúdo do PDF
            
        Returns:
            Tuple[texto, confiança=0]
        """
        try:
            from PyPDF2 import PdfReader
            import io
            
            reader = PdfReader(io.BytesIO(file_content))
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() or ""
                text += "\n\n"
            
            return text.strip(), 0
            
        except Exception:
            return "[Texto extraído via OCR - Tesseract não disponível]", 0


# Singleton instance
ocr_service = OCRService()
