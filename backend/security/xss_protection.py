"""
Proteção contra XSS (Cross-Site Scripting)
Sanitização de inputs e outputs
"""

import bleach
from bleach.css_sanitizer import CSSSanitizer
from html import escape
import re

# Configuração padrão do bleach para conteúdo seguro
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    '*': ['class']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html_input(text: str) -> str:
    """
    Sanitiza input HTML removendo tags e atributos perigosos
    Usar para campos que aceitam rich text
    """
    if not text:
        return text
    
    try:
        cleaned = bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True  # Remove tags não permitidas em vez de escapar
        )
        return cleaned
    except Exception as e:
        print(f"Erro na sanitização HTML: {e}")
        return escape(text)  # Fallback: escapar tudo


def sanitize_plain_text(text: str) -> str:
    """
    Escapa completamente HTML para campos de texto plano
    Usar para títulos, nomes, descrições simples
    """
    if not text:
        return text
    
    # Remove tags HTML completamente
    text = re.sub(r'<[^>]+>', '', text)
    # Escapa caracteres especiais
    return escape(text)


def sanitize_ai_output(text: str) -> str:
    """
    Sanitiza saída da IA antes de salvar no banco
    Remove scripts, eventos onclick, etc
    """
    if not text:
        return text
    
    # Padrões perigosos para remover
    dangerous_patterns = [
        (r'<script[^>]*>.*?</script>', '', re.DOTALL | re.IGNORECASE),
        (r'javascript:', '', re.IGNORECASE),
        (r'on\w+\s*=\s*["\'][^"\']*["\']', '', re.IGNORECASE),
        (r'<iframe[^>]*>.*?</iframe>', '', re.DOTALL | re.IGNORECASE),
        (r'<object[^>]*>.*?</object>', '', re.DOTALL | re.IGNORECASE),
        (r'<embed[^>]*>', '', re.IGNORECASE),
        (r'data:text/html[^,]*,', '', re.IGNORECASE),
    ]
    
    cleaned = text
    for pattern, replacement, flags in dangerous_patterns:
        cleaned = re.sub(pattern, replacement, cleaned, flags=flags)
    
    # Depois aplicar bleach
    return sanitize_html_input(cleaned)


def sanitize_sql_input(text: str) -> str:
    """
    Remove caracteres que podem ser usados em SQL injection
    """
    if not text:
        return text
    
    # Remove aspas simples duplas (escaping) e caracteres de controle SQL
    dangerous = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_', 'union', 'select', 'insert', 'delete', 'drop']
    
    cleaned = text
    for char in dangerous:
        cleaned = cleaned.replace(char, '')
    
    return cleaned


def validate_no_html(text: str) -> bool:
    """
    Verifica se texto contém tags HTML
    Útil para validação de campos que devem ser texto puro
    """
    if not text:
        return True
    
    html_pattern = re.compile(r'<[^>]+>')
    return not bool(html_pattern.search(text))


# Middleware para sanitização automática
class SanitizationMiddleware:
    """
    Middleware que sanitiza automaticamente inputs da requisição
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Sanitizar apenas em requisições HTTP
        if scope["type"] == "http":
            # Processar o body para sanitização
            # Nota: Implementação completa requer parsing do body
            pass
        
        await self.app(scope, receive, send)


def sanitize_dict(data: dict, html_fields: list = None, text_fields: list = None) -> dict:
    """
    Sanitiza todos os campos de um dicionário
    
    Args:
        data: Dicionário com dados
        html_fields: Campos que aceitam HTML (rich text)
        text_fields: Campos de texto puro (default: todos os não-html)
    """
    if not data:
        return data
    
    result = {}
    html_fields = html_fields or []
    text_fields = text_fields or []
    
    for key, value in data.items():
        if isinstance(value, str):
            if key in html_fields:
                result[key] = sanitize_html_input(value)
            elif key in text_fields or not html_fields:
                result[key] = sanitize_plain_text(value)
            else:
                result[key] = sanitize_plain_text(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, html_fields, text_fields)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item, html_fields, text_fields) if isinstance(item, dict)
                else sanitize_plain_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result
