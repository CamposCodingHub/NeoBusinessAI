"""
Pipeline de Document AI em 7 Estágios
=====================================
Arquitetura baseada em referências enterprise (SAP, Snowflake, AWS)

Estágios:
1. Ingestion - Aceita documentos de múltiplas fontes
2. Format Normalization - Converte para formato canônico
3. Layout Detection - Identifica regiões (texto, tabelas, figuras)
4. OCR - Extrai texto com bounding boxes
5. Structure Parsing - Reconstrói ordem de leitura e hierarquia
6. Semantic Extraction - Extrai dados estruturados
7. Validation - Valida contra regras de negócio
"""

import os
import hashlib
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Tipos de documentos suportados"""
    PDF = "pdf"
    IMAGE = "image"
    DOCX = "docx"
    TXT = "txt"
    UNKNOWN = "unknown"


class ProcessingStage(Enum):
    """Estágios do pipeline"""
    INGESTION = "ingestion"
    NORMALIZATION = "normalization"
    LAYOUT_DETECTION = "layout_detection"
    OCR = "ocr"
    STRUCTURE_PARSING = "structure_parsing"
    SEMANTIC_EXTRACTION = "semantic_extraction"
    VALIDATION = "validation"


@dataclass
class DocumentMetadata:
    """Metadados do documento"""
    filename: str
    file_type: DocumentType
    file_size: int
    file_hash: str
    page_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineResult:
    """Resultado do pipeline"""
    success: bool
    metadata: DocumentMetadata
    extracted_text: str
    structured_data: Dict[str, Any]
    confidence_score: float
    processing_time_ms: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stage_results: Dict[ProcessingStage, Any] = field(default_factory=dict)


class DocumentPipeline:
    """
    Pipeline de processamento de documentos em 7 estágios
    """
    
    def __init__(self):
        self.cache_enabled = True
        self.ocr_engine = None
        self.layout_detector = None
        self.semantic_extractor = None
        
    async def process(self, file_path: str, file_content: bytes) -> PipelineResult:
        """
        Processa documento através dos 7 estágios
        """
        start_time = datetime.utcnow()
        
        try:
            # Estágio 1: Ingestion
            metadata = await self._stage_ingestion(file_path, file_content)
            
            # Estágio 2: Format Normalization
            normalized_content = await self._stage_normalization(file_content, metadata)
            
            # Estágio 3: Layout Detection
            layout_info = await self._stage_layout_detection(normalized_content, metadata)
            
            # Estágio 4: OCR
            ocr_result = await self._stage_ocr(normalized_content, layout_info, metadata)
            
            # Estágio 5: Structure Parsing
            parsed_structure = await self._stage_structure_parsing(ocr_result, layout_info, metadata)
            
            # Estágio 6: Semantic Extraction
            structured_data = await self._stage_semantic_extraction(parsed_structure, metadata)
            
            # Estágio 7: Validation
            validation_result = await self._stage_validation(structured_data, metadata)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return PipelineResult(
                success=True,
                metadata=metadata,
                extracted_text=ocr_result.get('text', ''),
                structured_data=structured_data,
                confidence_score=validation_result.get('confidence', 0.0),
                processing_time_ms=int(processing_time),
                stage_results={
                    ProcessingStage.INGESTION: metadata,
                    ProcessingStage.NORMALIZATION: normalized_content,
                    ProcessingStage.LAYOUT_DETECTION: layout_info,
                    ProcessingStage.OCR: ocr_result,
                    ProcessingStage.STRUCTURE_PARSING: parsed_structure,
                    ProcessingStage.SEMANTIC_EXTRACTION: structured_data,
                    ProcessingStage.VALIDATION: validation_result
                }
            )
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return PipelineResult(
                success=False,
                metadata=DocumentMetadata(
                    filename=os.path.basename(file_path),
                    file_type=DocumentType.UNKNOWN,
                    file_size=len(file_content),
                    file_hash=hashlib.sha256(file_content).hexdigest()
                ),
                extracted_text="",
                structured_data={},
                confidence_score=0.0,
                processing_time_ms=int(processing_time),
                errors=[str(e)]
            )
    
    async def _stage_ingestion(self, file_path: str, file_content: bytes) -> DocumentMetadata:
        """
        Estágio 1: Ingestion
        Aceita documentos de múltiplas fontes e persiste em storage
        """
        logger.info(f"[STAGE 1] Ingestion: {file_path}")
        
        # Detectar tipo de arquivo
        file_ext = os.path.splitext(file_path)[1].lower()
        file_type_map = {
            '.pdf': DocumentType.PDF,
            '.jpg': DocumentType.IMAGE,
            '.jpeg': DocumentType.IMAGE,
            '.png': DocumentType.IMAGE,
            '.docx': DocumentType.DOCX,
            '.txt': DocumentType.TXT
        }
        file_type = file_type_map.get(file_ext, DocumentType.UNKNOWN)
        
        # Calcular hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Contar páginas (para PDF)
        page_count = 0
        if file_type == DocumentType.PDF:
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(file_content)
                page_count = len(pdf_reader.pages)
            except:
                pass
        
        return DocumentMetadata(
            filename=os.path.basename(file_path),
            file_type=file_type,
            file_size=len(file_content),
            file_hash=file_hash,
            page_count=page_count
        )
    
    async def _stage_normalization(self, file_content: bytes, metadata: DocumentMetadata) -> bytes:
        """
        Estágio 2: Format Normalization
        Converte entradas heterogêneas para formato canônico (imagens de página)
        """
        logger.info(f"[STAGE 2] Normalization: {metadata.filename}")
        
        # Se já é PDF, retorna como está
        if metadata.file_type == DocumentType.PDF:
            return file_content
        
        # Se é imagem, converte para PDF
        if metadata.file_type == DocumentType.IMAGE:
            try:
                from PIL import Image
                import io
                
                img = Image.open(io.BytesIO(file_content))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Converter para PDF
                pdf_bytes = io.BytesIO()
                img.save(pdf_bytes, format='PDF')
                return pdf_bytes.getvalue()
            except Exception as e:
                logger.warning(f"Image to PDF conversion failed: {e}")
                return file_content
        
        # DOCX para PDF
        if metadata.file_type == DocumentType.DOCX:
            # Implementação futura com docx2pdf
            logger.warning("DOCX to PDF conversion not implemented yet")
            return file_content
        
        return file_content
    
    async def _stage_layout_detection(self, content: bytes, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Estágio 3: Layout Detection
        Identifica regiões: blocos de texto, tabelas, figuras, assinaturas
        """
        logger.info(f"[STAGE 3] Layout Detection: {metadata.filename}")
        
        layout_info = {
            'text_blocks': [],
            'tables': [],
            'figures': [],
            'signatures': [],
            'headers': [],
            'footers': []
        }
        
        # Implementação básica - pode ser expandida com LayoutLMv3
        if metadata.file_type == DocumentType.PDF:
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(content)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        layout_info['text_blocks'].append({
                            'page': page_num,
                            'text': text,
                            'bbox': [0, 0, 0, 0]  # Placeholder
                        })
            except Exception as e:
                logger.warning(f"Layout detection failed: {e}")
        
        return layout_info
    
    async def _stage_ocr(self, content: bytes, layout_info: Dict, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Estágio 4: OCR
        Converte regiões de texto em sequências de caracteres com bounding boxes
        """
        logger.info(f"[STAGE 4] OCR: {metadata.filename}")
        
        ocr_result = {
            'text': '',
            'confidence': 0.0,
            'pages': []
        }
        
        try:
            from tools.ocr_real import process_uploaded_file
            import io
            
            # Usar OCR existente
            result = await process_uploaded_file(io.BytesIO(content), metadata.filename)
            
            if result:
                ocr_result['text'] = result.get('text', '')
                ocr_result['confidence'] = result.get('confidence', 0.8)
                ocr_result['pages'] = result.get('pages', [])
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            # Fallback para extração simples de PDF
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(content)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                ocr_result['text'] = text
                ocr_result['confidence'] = 0.7
            except:
                pass
        
        return ocr_result
    
    async def _stage_structure_parsing(self, ocr_result: Dict, layout_info: Dict, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Estágio 5: Structure Parsing
        Reconstrói ordem de leitura, estrutura de tabelas e hierarquia do documento
        """
        logger.info(f"[STAGE 5] Structure Parsing: {metadata.filename}")
        
        parsed_structure = {
            'reading_order': [],
            'tables': [],
            'hierarchy': {
                'title': '',
                'sections': [],
                'subsections': []
            },
            'paragraphs': []
        }
        
        text = ocr_result.get('text', '')
        
        # Dividir em parágrafos
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        parsed_structure['paragraphs'] = paragraphs
        
        # Detectar título (primeira linha em maiúsculas)
        if paragraphs:
            first_line = paragraphs[0].split('\n')[0]
            if first_line.isupper() or len(first_line) < 100:
                parsed_structure['hierarchy']['title'] = first_line
        
        # Detectar seções (linhas em maiúsculas)
        for para in paragraphs:
            lines = para.split('\n')
            for line in lines:
                if line.isupper() and len(line) < 100:
                    parsed_structure['hierarchy']['sections'].append(line)
        
        parsed_structure['reading_order'] = paragraphs
        
        return parsed_structure
    
    async def _stage_semantic_extraction(self, parsed_structure: Dict, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Estágio 6: Semantic Extraction
        Produz dados estruturados conformes ao schema (prazos, valores, partes)
        """
        logger.info(f"[STAGE 6] Semantic Extraction: {metadata.filename}")
        
        structured_data = {
            'deadlines': [],
            'values': [],
            'dates': [],
            'parties': [],
            'summary': '',
            'key_points': [],
            'risks': [],
            'recommendations': []
        }
        
        text = '\n'.join(parsed_structure.get('paragraphs', []))
        
        # Usar IA para extração semântica
        try:
            from ai.lexscan_engine import lexscan_engine
            
            # Extrair prazos
            deadlines = await lexscan_engine.extract_deadlines(text)
            structured_data['deadlines'] = deadlines
            
            # Extrair valores
            values = await lexscan_engine.extract_values(text)
            structured_data['values'] = values
            
            # Extrair datas
            dates = await lexscan_engine.extract_dates(text)
            structured_data['dates'] = dates
            
            # Gerar resumo
            summary = await lexscan_engine.generate_summary(text)
            structured_data['summary'] = summary
            
            # Extrair pontos chave
            key_points = await lexscan_engine.extract_key_points(text)
            structured_data['key_points'] = key_points
            
        except Exception as e:
            logger.warning(f"Semantic extraction with AI failed: {e}")
            # Fallback para extração baseada em regex
            structured_data = self._fallback_extraction(text)
        
        return structured_data
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Extração baseada em regex como fallback"""
        import re
        
        structured_data = {
            'deadlines': [],
            'values': [],
            'dates': [],
            'parties': [],
            'summary': text[:500] + '...' if len(text) > 500 else text,
            'key_points': [],
            'risks': [],
            'recommendations': []
        }
        
        # Extrair datas (formato brasileiro)
        date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'
        dates = re.findall(date_pattern, text)
        structured_data['dates'] = dates
        
        # Extrair valores monetários
        value_pattern = r'R\$\s*[\d.,]+'
        values = re.findall(value_pattern, text)
        structured_data['values'] = values
        
        return structured_data
    
    async def _stage_validation(self, structured_data: Dict, metadata: DocumentMetadata) -> Dict[str, Any]:
        """
        Estágio 7: Validation
        Valida dados extraídos contra regras de negócio
        """
        logger.info(f"[STAGE 7] Validation: {metadata.filename}")
        
        validation_result = {
            'is_valid': True,
            'confidence': 0.8,
            'errors': [],
            'warnings': [],
            'checks': {
                'has_deadlines': len(structured_data.get('deadlines', [])) > 0,
                'has_values': len(structured_data.get('values', [])) > 0,
                'has_summary': bool(structured_data.get('summary')),
                'has_dates': len(structured_data.get('dates', [])) > 0
            }
        }
        
        # Calcular confiança baseada em checks
        passed_checks = sum(validation_result['checks'].values())
        total_checks = len(validation_result['checks'])
        validation_result['confidence'] = passed_checks / total_checks if total_checks > 0 else 0.0
        
        # Regras de validação
        if not structured_data.get('summary'):
            validation_result['warnings'].append('No summary generated')
        
        if not structured_data.get('deadlines'):
            validation_result['warnings'].append('No deadlines detected')
        
        # Se confiança muito baixa, marcar para revisão humana
        if validation_result['confidence'] < 0.5:
            validation_result['is_valid'] = False
            validation_result['errors'].append('Low confidence score - requires human review')
        
        return validation_result


# Instância global do pipeline
document_pipeline = DocumentPipeline()
