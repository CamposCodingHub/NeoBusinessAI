"""
Sanitizadores e Validadores de Input
=====================================
Proteção contra SQL Injection, XSS, Path Traversal e outros ataques de injeção.
"""

import re
import html
import uuid
from typing import Optional, List, Pattern
import logging

logger = logging.getLogger(__name__)


# ==================== PATTERNS DE ATAQUE ====================

# Patterns SQL Injection
SQL_INJECTION_PATTERNS: List[Pattern] = [
    re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|UNION|UNION\s+ALL)\b)", re.IGNORECASE),
    re.compile(r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    re.compile(r"(--|#|/\*|\*/|;)", re.IGNORECASE),
    re.compile(r"(\b(WAITFOR|DELAY|SHUTDOWN|BENCHMARK|PG_SLEEP|SLEEP)\b)", re.IGNORECASE),
    re.compile(r"('\"\s*OR\s*['\"]?\d+['\"]?=\s*['\"]?\d+)", re.IGNORECASE),
    re.compile(r"(\b(CHAR|NCHAR|VARCHAR|NVARCHAR)\s*\(\s*\d+\s*\))", re.IGNORECASE),
]

# Patterns XSS
XSS_PATTERNS: List[Pattern] = [
    re.compile(r"<script[^>]*>[\s\S]*?</script>", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick, onload, etc
    re.compile(r"<iframe", re.IGNORECASE),
    re.compile(r"<object", re.IGNORECASE),
    re.compile(r"<embed", re.IGNORECASE),
    re.compile(r"data:text/html", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),  # CSS expressions
]

# Patterns Path Traversal
PATH_TRAVERSAL_PATTERNS: List[Pattern] = [
    re.compile(r"\.\./|\.\.\\"),  # ../ or ..\
    re.compile(r"%2e%2e%2f", re.IGNORECASE),  # URL encoded ../
    re.compile(r"%252e%252e%252f", re.IGNORECASE),  # Double URL encoded
    re.compile(r"\.\.\/|\.{2,}/"),  # Unicode variations
]

# Patterns de Command Injection
COMMAND_INJECTION_PATTERNS: List[Pattern] = [
    re.compile(r"[;&|`]\s*(\b(ping|nc|netcat|wget|curl|bash|sh|cmd|powershell|python|perl|ruby)\b)", re.IGNORECASE),
    re.compile(r"\$\([^)]*\)"),  # $(command)
    re.compile(r"`[^`]*`"),  # `command`
]


# ==================== SANITIZAÇÃO BÁSICA ====================

def sanitize_input(input_str: str, max_length: int = 1000, 
                   allow_html: bool = False) -> str:
    """
    Sanitização geral de input
    
    Args:
        input_str: String a ser sanitizada
        max_length: Comprimento máximo permitido
        allow_html: Se True, preserva tags HTML seguras
    
    Returns:
        String sanitizada
    """
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Remover null bytes
    input_str = input_str.replace('\x00', '')
    
    # Limitar tamanho
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
        logger.warning(f"Input truncado para {max_length} caracteres")
    
    # Remover caracteres de controle (exceto newline/tab)
    input_str = ''.join(char for char in input_str if ord(char) >= 32 or char in '\n\t\r')
    
    if not allow_html:
        # Escapar HTML
        input_str = html.escape(input_str)
    
    return input_str.strip()


def sanitize_sql(value: str, strict: bool = True) -> str:
    """
    Sanitização para queries SQL
    
    ATENÇÃO: Sempre use prepared statements/parameterized queries!
    Esta função é apenas uma camada adicional de defesa.
    
    Args:
        value: Valor a ser sanitizado
        strict: Se True, bloqueia mais agressivamente
    
    Returns:
        Valor sanitizado ou levanta exceção se detectar ataque
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Verificar patterns de SQL injection
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            logger.warning(f"Possível SQL Injection detectado: {hash_sensitive(value)}")
            if strict:
                raise ValueError("Input contém caracteres potencialmente perigosos")
    
    # Remover caracteres especiais SQL
    dangerous_chars = ";'\"--/*"
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    return value.strip()


def sanitize_html(content: str, allowed_tags: Optional[List[str]] = None) -> str:
    """
    Sanitização de HTML - permite apenas tags seguras
    
    Args:
        content: Conteúdo HTML
        allowed_tags: Lista de tags permitidas (default: p, br, strong, em, u, h1-h6)
    
    Returns:
        HTML sanitizado
    """
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a']
    
    # Se não for HTML, apenas escapar
    if '<' not in content:
        return html.escape(content)
    
    # Remover scripts e event handlers
    for pattern in XSS_PATTERNS:
        content = pattern.sub('', content)
    
    # Parser simples para remover tags não permitidas
    import re
    
    def replace_tag(match):
        tag = match.group(1).lower()
        if tag in allowed_tags:
            return match.group(0)  # Manter tag permitida
        return ''  # Remover tag não permitida
    
    # Remover tags não permitidas (preservar conteúdo interno para algumas)
    content = re.sub(r'<([^>\s]+)[^>]*>', replace_tag, content, flags=re.IGNORECASE)
    content = re.sub(r'</([^>\s]+)>', replace_tag, content, flags=re.IGNORECASE)
    
    return content


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    Validação de caminho de arquivo seguro
    
    Args:
        file_path: Caminho do arquivo a validar
        allowed_extensions: Lista de extensões permitidas (ex: ['.pdf', '.jpg'])
    
    Returns:
        True se o caminho é válido e seguro, False caso contrário
    """
    if not file_path or not isinstance(file_path, str):
        return False
    
    # Verificar path traversal
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if pattern.search(file_path):
            logger.warning(f"Path traversal detectado em: {hash_sensitive(file_path)}")
            return False
    
    # Verificar caracteres nulos
    if '\x00' in file_path:
        return False
    
    # Validar extensão se especificado
    if allowed_extensions:
        ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
        if f'.{ext}' not in [e.lower() for e in allowed_extensions]:
            return False
    
    # Verificar comprimento
    if len(file_path) > 4096:
        return False
    
    return True


def sanitize_file_path(filename: str, allowed_extensions: Optional[List[str]] = None) -> str:
    """
    Sanitização de caminho de arquivo
    
    Args:
        filename: Nome do arquivo
        allowed_extensions: Lista de extensões permitidas
    
    Returns:
        Nome de arquivo sanitizado
    
    Raises:
        ValueError: Se detectar path traversal ou extensão não permitida
    """
    if not filename:
        raise ValueError("Nome de arquivo não pode ser vazio")
    
    # Verificar path traversal
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if pattern.search(filename):
            logger.error(f"Path Traversal detectado: {hash_sensitive(filename)}")
            raise ValueError("Nome de arquivo contém caracteres inválidos")
    
    # Remover caminhos absolutos
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remover caracteres especiais
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    # Validar extensão
    if allowed_extensions:
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{ext}' not in [e.lower() for e in allowed_extensions]:
            raise ValueError(f"Extensão .{ext} não permitida")
    
    # Limitar tamanho
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
    
    return filename


def sanitize_command_arg(arg: str) -> str:
    """
    Sanitização para argumentos de comando (prevenção de command injection)
    
    Args:
        arg: Argumento de comando
    
    Returns:
        Argumento sanitizado
    """
    if not isinstance(arg, str):
        arg = str(arg)
    
    # Verificar command injection
    for pattern in COMMAND_INJECTION_PATTERNS:
        if pattern.search(arg):
            logger.error(f"Command Injection detectado: {hash_sensitive(arg)}")
            raise ValueError("Argumento contém caracteres perigosos")
    
    # Escapar caracteres especiais de shell
    dangerous = ';|&`$(){}[]<>!\\"\''
    for char in dangerous:
        arg = arg.replace(char, '')
    
    return arg.strip()


# ==================== VALIDAÇÕES ====================

def validate_email(email: str) -> bool:
    """
    Validação de email com regex seguro
    
    Args:
        email: Email a ser validado
    
    Returns:
        True se válido, False caso contrário
    """
    if not email or len(email) > 254:
        return False
    
    pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if not pattern.match(email):
        return False
    
    # Verificar partes do email
    try:
        local, domain = email.rsplit('@', 1)
        if len(local) > 64 or len(domain) > 255:
            return False
    except ValueError:
        return False
    
    return True


def validate_uuid(value: str, version: int = 4) -> bool:
    """
    Validação de UUID
    
    Args:
        value: UUID a ser validado
        version: Versão do UUID (4 por padrão)
    
    Returns:
        True se válido, False caso contrário
    """
    try:
        uuid_obj = uuid.UUID(value, version=version)
        return str(uuid_obj) == value
    except (ValueError, TypeError):
        return False


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validação de senha forte
    
    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos uma maiúscula
    - Pelo menos uma minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    
    Args:
        password: Senha a ser validada
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos um número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos um caractere especial"
    
    # Verificar padrões comuns fracos
    common_patterns = ['123456', 'password', 'qwerty', 'abc123']
    if any(pattern in password.lower() for pattern in common_patterns):
        return False, "Senha muito comum e insegura"
    
    return True, "Senha válida"


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
    """
    Validação segura de URL
    
    Args:
        url: URL a ser validada
        allowed_schemes: Lista de schemes permitidos (default: http, https)
    
    Returns:
        True se válida e segura, False caso contrário
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    if not url or len(url) > 2048:
        return False
    
    # Verificar scheme
    scheme_match = re.match(r'^([a-zA-Z][a-zA-Z0-9+.-]*)://', url)
    if not scheme_match:
        return False
    
    scheme = scheme_match.group(1).lower()
    if scheme not in allowed_schemes:
        return False
    
    # Bloquear IPs privados (SSRF prevention)
    private_ip_patterns = [
        r'127\.\d+\.\d+\.\d+',
        r'10\.\d+\.\d+\.\d+',
        r'172\.1[6-9]\.\d+\.\d+',
        r'172\.2[0-9]\.\d+\.\d+',
        r'172\.3[0-1]\.\d+\.\d+',
        r'192\.168\.\d+\.\d+',
        r'0\.0\.0\.0',
        r'::1',
        r'fc00:',
        r'fe80:',
    ]
    
    for pattern in private_ip_patterns:
        if re.search(pattern, url):
            logger.warning(f"Tentativa de acesso a IP privado bloqueada: {hash_sensitive(url)}")
            return False
    
    return True


# ==================== FUNÇÕES UTILITÁRIAS ====================

def hash_sensitive(value: str, visible_chars: int = 4) -> str:
    """
    Hash para logging de dados sensíveis
    
    Args:
        value: Valor sensível
        visible_chars: Número de caracteres visíveis no início
    
    Returns:
        String parcialmente mascarada
    """
    import hashlib
    
    if not value:
        return ""
    
    # Mostrar primeiros N caracteres + hash
    visible = value[:visible_chars]
    hash_part = hashlib.sha256(value.encode()).hexdigest()[:8]
    
    return f"{visible}...[{hash_part}]"


def remove_invisible_chars(text: str) -> str:
    """Remove caracteres invisíveis e de controle perigosos"""
    # Manter apenas caracteres imprimíveis, newline, tab
    allowed = set(range(32, 127)) | {9, 10, 13}
    return ''.join(c for c in text if ord(c) in allowed)


def normalize_unicode(text: str) -> str:
    """Normaliza unicode para prevenir homograph attacks"""
    import unicodedata
    return unicodedata.normalize('NFKC', text)


# ==================== DECORATORS ====================

def check_sql_injection(func):
    """Decorator para verificar SQL injection em argumentos"""
    def wrapper(*args, **kwargs):
        # Verificar todos os argumentos string
        for arg in list(args) + list(kwargs.values()):
            if isinstance(arg, str):
                for pattern in SQL_INJECTION_PATTERNS:
                    if pattern.search(arg):
                        raise ValueError("Input contém padrões de SQL injection")
        return func(*args, **kwargs)
    return wrapper


def check_xss(func):
    """Decorator para verificar XSS em argumentos"""
    def wrapper(*args, **kwargs):
        for arg in list(args) + list(kwargs.values()):
            if isinstance(arg, str):
                for pattern in XSS_PATTERNS:
                    if pattern.search(arg):
                        raise ValueError("Input contém padrões de XSS")
        return func(*args, **kwargs)
    return wrapper
