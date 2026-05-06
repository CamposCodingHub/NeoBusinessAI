"""
OCR Real com Tesseract - LexScan IA
Processa PDFs e imagens extraindo texto completo
"""

import io
import os
from typing import Dict, List, Optional, Union
from PIL import Image
import pytesseract

# Configuração do Tesseract para Windows
# Se estiver em outro SO, ajustar o caminho
if os.name == 'nt':  # Windows
    # Tenta encontrar Tesseract em locais comuns
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\%USERNAME%\AppData\Local\Tesseract-OCR\tesseract.exe',
    ]
    
    tesseract_path = None
    for path in possible_paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            tesseract_path = expanded_path
            break
    
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        print(f"[OCR] Tesseract encontrado em: {tesseract_path}")
    else:
        print("[OCR AVISO] Tesseract não encontrado. OCR pode não funcionar.")
        print("[OCR] Baixe em: https://github.com/UB-Mannheim/tesseract/wiki")

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
    print("[OCR] pdf2image disponível")
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("[OCR] pdf2image não disponível - instale com: pip install pdf2image")


class RealOCRProcessor:
    """Processa documentos reais com Tesseract OCR"""
    
    def __init__(self):
        self.tesseract_available = self._check_tesseract()
        
    def _check_tesseract(self) -> bool:
        """Verifica se Tesseract está disponível"""
        try:
            pytesseract.get_tesseract_version()
            print(f"[OCR] Tesseract versão: {pytesseract.get_tesseract_version()}")
            return True
        except Exception as e:
            print(f"[OCR] Tesseract não disponível: {e}")
            return False
    
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extrai texto de imagem usando Tesseract
        
        Args:
            image_bytes: Bytes da imagem
            
        Returns:
            Texto extraído
        """
        if not self.tesseract_available:
            return "[ERRO] Tesseract OCR não está instalado"
        
        try:
            # Abrir imagem
            image = Image.open(io.BytesIO(image_bytes))
            
            # Converter para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Configurações otimizadas para português
            config = '--oem 3 --psm 6 -l por+eng'
            
            # Extrair texto
            text = pytesseract.image_to_string(image, config=config)
            
            return text.strip()
            
        except Exception as e:
            print(f"[OCR ERROR] {e}")
            return f"[ERRO] Falha ao processar imagem: {str(e)}"
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extrai texto de PDF convertendo para imagens
        
        Args:
            pdf_bytes: Bytes do PDF
            
        Returns:
            Texto extraído de todas as páginas
        """
        if not self.tesseract_available:
            return "[ERRO] Tesseract OCR não está instalado"
        
        if not PDF2IMAGE_AVAILABLE:
            return "[ERRO] pdf2image não está instalado. Instale com: pip install pdf2image"
        
        try:
            # Converter PDF para imagens
            print(f"[OCR] Convertendo PDF ({len(pdf_bytes)} bytes) para imagens...")
            
            images = convert_from_bytes(
                pdf_bytes,
                dpi=300,  # Alta resolução para melhor OCR
                fmt='png'
            )
            
            print(f"[OCR] PDF tem {len(images)} páginas")
            
            # Extrair texto de cada página
            all_text = []
            config = '--oem 3 --psm 6 -l por+eng'
            
            for i, image in enumerate(images):
                print(f"[OCR] Processando página {i+1}/{len(images)}...")
                
                # Extrair texto
                text = pytesseract.image_to_string(image, config=config)
                all_text.append(f"\n--- PÁGINA {i+1} ---\n{text}")
            
            return "\n".join(all_text).strip()
            
        except Exception as e:
            print(f"[OCR ERROR] {e}")
            return f"[ERRO] Falha ao processar PDF: {str(e)}"
    
    def process_document(self, file_bytes: bytes, filename: str, manual_text: str = None) -> Dict:
        """
        Processa qualquer tipo de documento
        
        Args:
            file_bytes: Bytes do arquivo
            filename: Nome do arquivo
            manual_text: Texto manual se OCR não disponível
            
        Returns:
            Dicionário com texto extraído e metadados
        """
        # Se tem texto manual, usar ele
        if manual_text:
            return {
                'success': True,
                'filename': filename,
                'type': 'manual',
                'text': manual_text,
                'pages': 1,
                'method': 'manual_input'
            }
        
        # Se Tesseract não disponível, retornar erro com instruções
        if not self.tesseract_available:
            return {
                'success': False,
                'filename': filename,
                'type': 'ocr_unavailable',
                'text': '',
                'error': 'Tesseract OCR não está instalado. Baixe em: https://github.com/UB-Mannheim/tesseract/wiki',
                'ocr_available': False
            }
        
        # Detectar tipo de arquivo
        file_lower = filename.lower()
        
        # Extensões de imagem
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp']
        
        # Extensões de PDF
        pdf_extensions = ['.pdf']
        
        is_image = any(file_lower.endswith(ext) for ext in image_extensions)
        is_pdf = any(file_lower.endswith(ext) for ext in pdf_extensions)
        
        print(f"[OCR] Processando: {filename}")
        print(f"[OCR] Tipo detectado: {'Imagem' if is_image else 'PDF' if is_pdf else 'Desconhecido'}")
        
        if is_image:
            text = self.extract_text_from_image(file_bytes)
            return {
                'success': True,
                'filename': filename,
                'type': 'image',
                'text': text,
                'pages': 1,
                'method': 'tesseract_ocr'
            }
        
        elif is_pdf:
            text = self.extract_text_from_pdf(file_bytes)
            # Contar páginas aproximadas
            pages = text.count('--- PÁGINA')
            return {
                'success': True,
                'filename': filename,
                'type': 'pdf',
                'text': text,
                'pages': pages if pages > 0 else 1,
                'method': 'tesseract_ocr_pdf'
            }
        
        else:
            return {
                'success': False,
                'filename': filename,
                'type': 'unknown',
                'text': '',
                'error': 'Formato não suportado. Use PDF, JPG, PNG, TIFF.'
            }


# Instância global
ocr_real = RealOCRProcessor()


def process_uploaded_file(file_bytes: bytes, filename: str) -> Dict:
    """
    Função convenience para processar arquivo uploadado
    
    Args:
        file_bytes: Bytes do arquivo
        filename: Nome do arquivo
        
    Returns:
        Resultado do processamento OCR
    """
    return ocr_real.process_document(file_bytes, filename)


if __name__ == "__main__":
    # Teste
    print("=" * 50)
    print("TESTE OCR REAL")
    print("=" * 50)
    
    # Verificar Tesseract
    if ocr_real.tesseract_available:
        print("✅ Tesseract está disponível!")
        
        # Testar com texto simples
        from PIL import Image, ImageDraw, ImageFont
        
        # Criar imagem de teste
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Tentar usar fonte padrão
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 10), "Processo nº 12345-67.2024.8.26.0001", fill='black', font=font)
        draw.text((10, 40), "Autor: João Silva", fill='black', font=font)
        draw.text((10, 70), "Prazo: 15 dias", fill='black', font=font)
        
        # Salvar em bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Testar OCR
        result = ocr_real.process_document(img_bytes.read(), "teste.png")
        
        print(f"\nResultado:")
        print(f"Sucesso: {result['success']}")
        print(f"Texto extraído:\n{result['text']}")
        
    else:
        print("❌ Tesseract não está disponível")
        print("Instale em: https://github.com/UB-Mannheim/tesseract/wiki")
