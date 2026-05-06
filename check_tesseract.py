#!/usr/bin/env python3
"""
Script para verificar instalação do Tesseract OCR
"""

import os
import sys

def check_tesseract():
    """Verifica se Tesseract está instalado"""
    
    print("=" * 60)
    print("VERIFICAÇÃO DO TESSERACT OCR")
    print("=" * 60)
    
    # Verificar se pytesseract está instalado
    try:
        import pytesseract
        print("✅ pytesseract instalado")
    except ImportError:
        print("❌ pytesseract NÃO instalado")
        print("   Instale com: pip install pytesseract")
        return False
    
    # Verificar se PIL está instalado
    try:
        from PIL import Image
        print("✅ Pillow (PIL) instalado")
    except ImportError:
        print("❌ Pillow NÃO instalado")
        print("   Instale com: pip install Pillow")
        return False
    
    # Verificar se pdf2image está instalado
    try:
        from pdf2image import convert_from_path
        print("✅ pdf2image instalado")
    except ImportError:
        print("❌ pdf2image NÃO instalado")
        print("   Instale com: pip install pdf2image")
        return False
    
    # Verificar Tesseract
    print("\n" + "=" * 60)
    print("VERIFICANDO TESSERACT")
    print("=" * 60)
    
    tesseract_found = False
    
    if os.name == 'nt':  # Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Tesseract encontrado em: {path}")
                tesseract_found = True
                
                # Configurar
                pytesseract.pytesseract.tesseract_cmd = path
                break
        
        if not tesseract_found:
            print("❌ Tesseract NÃO encontrado nos locais padrão")
            print("\n📝 INSTRUÇÕES DE INSTALAÇÃO:")
            print("1. Baixe o instalador em:")
            print("   https://github.com/UB-Mannheim/tesseract/wiki")
            print("\n2. Execute o instalador e mantenha o caminho padrão:")
            print("   C:\\Program Files\\Tesseract-OCR\\")
            print("\n3. Durante a instalação, selecione:")
            print("   ☑ Portuguese (por)")
            print("   ☑ English (eng)")
            print("\n4. Após instalar, reinicie o servidor LexScan")
    
    else:  # Linux/Mac
        try:
            import subprocess
            result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Tesseract encontrado em: {result.stdout.strip()}")
                tesseract_found = True
            else:
                print("❌ Tesseract não encontrado no PATH")
        except Exception as e:
            print(f"❌ Erro ao verificar: {e}")
    
    # Testar versão
    if tesseract_found:
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Versão do Tesseract: {version}")
        except Exception as e:
            print(f"⚠️ Não foi possível obter versão: {e}")
    
    print("\n" + "=" * 60)
    
    if tesseract_found:
        print("🎉 TUDO PRONTO! OCR está configurado corretamente.")
        print("=" * 60)
        return True
    else:
        print("⚠️ TESSERACT NÃO ESTÁ INSTALADO")
        print("=" * 60)
        print("\nO sistema funcionará em modo LIMITADO.")
        print("Para OCR completo, instale o Tesseract.")
        return False


if __name__ == "__main__":
    success = check_tesseract()
    sys.exit(0 if success else 1)
