"""
Validação de Upload de Arquivos - Segurança
Verificação de MIME type, magic numbers, extensões duplas
"""

import os
import magic
from fastapi import HTTPException, UploadFile
import io

# Magic numbers (assinaturas de arquivo)
MAGIC_NUMBERS = {
    b'%PDF': 'application/pdf',
    b'\x89PNG': 'image/png',
    b'\xff\xd8\xff': 'image/jpeg',
    b'PK\x03\x04': 'application/vnd.openxmlformats-officedocument',  # DOCX, XLSX
    b'\xd0\xcf\x11\xe0': 'application/msword',  # DOC, XLS antigo
    b'\x49\x49\x2a\x00': 'image/tiff',  # TIFF little-endian
    b'\x4d\x4d\x00\x2a': 'image/tiff',  # TIFF big-endian
}

# Extensões permitidas e seus MIME types
ALLOWED_TYPES = {
    '.pdf': ['application/pdf'],
    '.doc': ['application/msword'],
    '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    '.txt': ['text/plain'],
    '.rtf': ['application/rtf', 'text/rtf'],
    '.jpg': ['image/jpeg'],
    '.jpeg': ['image/jpeg'],
    '.png': ['image/png'],
    '.tiff': ['image/tiff'],
    '.tif': ['image/tiff'],
}

# Extensões perigosas (sempre bloquear)
DANGEROUS_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp', '.aspx',
    '.py', '.rb', '.pl', '.cgi', '.jar', '.war', '.ear', '.bin', '.scr',
    '.msi', '.vbs', '.js', '.wsf', '.ps1', '.htaccess', '.env'
}


async def validate_upload(file: UploadFile, max_size_mb: int = 50) -> dict:
    """
    Valida arquivo de upload com múltiplas camadas de segurança
    
    Retorna: {"valid": True, "mime_type": str, "safe_filename": str}
    ou levanta HTTPException
    """
    
    # 1. Verificar se arquivo foi enviado
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    filename = file.filename.lower()
    
    # 2. Verificar extensão dupla (ex: arquivo.pdf.exe)
    # Contar quantas extensões o arquivo tem
    parts = filename.split('.')
    if len(parts) > 2:
        # Verificar se a última parte é uma extensão perigosa
        last_ext = '.' + parts[-1]
        if last_ext in DANGEROUS_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail="Arquivo potencialmente perigoso detectado (extensão dupla)"
            )
    
    # 3. Verificar extensão principal
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext in DANGEROUS_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Extensão de arquivo não permitida: {file_ext}"
        )
    
    if file_ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Extensão não permitida. Use: {', '.join(ALLOWED_TYPES.keys())}"
        )
    
    # 4. Ler conteúdo para verificação
    content = await file.read()
    
    # 5. Verificar tamanho
    max_size_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=400, 
            detail=f"Arquivo muito grande. Máximo: {max_size_mb}MB"
        )
    
    # 6. Verificar magic numbers (assinatura do arquivo)
    detected_mime = None
    for magic_bytes, mime in MAGIC_NUMBERS.items():
        if content.startswith(magic_bytes):
            detected_mime = mime
            break
    
    # 7. Verificar com python-magic (libmagic)
    try:
        mime = magic.Magic(mime=True)
        libmagic_mime = mime.from_buffer(content[:4096])
        
        # Se detectamos magic numbers, comparar com libmagic
        if detected_mime and not libmagic_mime.startswith(detected_mime.split('/')[0]):
            raise HTTPException(
                status_code=400,
                detail="Conteúdo do arquivo não corresponde à extensão (possível arquivo disfarçado)"
            )
        
        detected_mime = libmagic_mime or detected_mime
        
    except Exception as e:
        # Se libmagic falhar, usar magic numbers
        pass
    
    # 8. Validar MIME type contra lista permitida
    allowed_mimes = ALLOWED_TYPES.get(file_ext, [])
    if detected_mime and not any(detected_mime.startswith(allowed.split('/')[0]) for allowed in allowed_mimes):
        raise HTTPException(
            status_code=400,
            detail=f"Conteúdo do arquivo ({detected_mime}) não corresponde à extensão {file_ext}"
        )
    
    # 9. Resetar posição do arquivo para leitura posterior
    await file.seek(0)
    
    # 10. Gerar nome seguro
    import uuid
    safe_name = f"{uuid.uuid4()}{file_ext}"
    
    return {
        "valid": True,
        "mime_type": detected_mime or allowed_mimes[0],
        "safe_filename": safe_name,
        "original_filename": file.filename,
        "content": content,
        "size": len(content)
    }


def sanitize_filename(filename: str) -> str:
    """Sanitiza nome de arquivo, remove caracteres perigosos"""
    import re
    # Remover caracteres que não são alfanuméricos, pontos, hífens ou underscores
    sanitized = re.sub(r'[^\w\.-]', '_', filename)
    # Remover sequências de pontos
    sanitized = re.sub(r'\.{2,}', '.', sanitized)
    # Limitar tamanho
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:250] + ext
    return sanitized
