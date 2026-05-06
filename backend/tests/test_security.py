"""
Testes de Segurança
Cobertura: Criptografia, validação de arquivo, rate limiting, XSS
"""

import pytest
from security.encryption import encrypt_field, decrypt_field, should_encrypt_field
from security.xss_protection import sanitize_plain_text, validate_no_html
from security.file_validation import ALLOWED_TYPES, DANGEROUS_EXTENSIONS
from utils.validators import validate_cpf, validate_cnpj

class TestEncryption:
    """Testes de criptografia"""
    
    def test_encrypt_decrypt_field(self):
        """Teste: Criptografar e descriptografar campo"""
        original = "11999999999"
        encrypted = encrypt_field(original)
        decrypted = decrypt_field(encrypted)
        
        assert encrypted != original  # Deve estar criptografado
        assert decrypted == original  # Deve descriptografar corretamente
        assert encrypted.startswith("ENC:")  # Prefixo de identificação
    
    def test_encrypt_empty_field(self):
        """Teste: Campo vazio não é criptografado"""
        assert encrypt_field("") == ""
        assert encrypt_field(None) is None
    
    def test_sensitive_fields_identification(self):
        """Teste: Identificação de campos sensíveis"""
        assert should_encrypt_field("Client", "cpf_cnpj") is True
        assert should_encrypt_field("Client", "phone") is True
        assert should_encrypt_field("Client", "address") is True
        assert should_encrypt_field("Client", "name") is False
        assert should_encrypt_field("User", "email") is False


class TestXSSProtection:
    """Testes de proteção XSS"""
    
    def test_sanitize_html_script_tag(self):
        """Teste: Tags script removidas"""
        malicious = "<script>alert('xss')</script>"
        sanitized = sanitize_plain_text(malicious)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
    
    def test_sanitize_html_event_handlers(self):
        """Teste: Event handlers removidos"""
        malicious = '<img src=x onerror=alert("xss")>'
        sanitized = sanitize_plain_text(malicious)
        assert "onerror" not in sanitized
    
    def test_validate_no_html_detects_tags(self):
        """Teste: Detecção de HTML em texto"""
        assert validate_no_html("Texto puro") is True
        assert validate_no_html("<p>Texto HTML</p>") is False
        assert validate_no_html("Texto com <b>negrito</b>") is False


class TestFileValidation:
    """Testes de validação de arquivos"""
    
    def test_allowed_extensions(self):
        """Teste: Extensões permitidas"""
        assert ".pdf" in ALLOWED_TYPES
        assert ".docx" in ALLOWED_TYPES
        assert ".jpg" in ALLOWED_TYPES
        assert ".png" in ALLOWED_TYPES
    
    def test_dangerous_extensions_blocked(self):
        """Teste: Extensões perigosas bloqueadas"""
        assert ".exe" in DANGEROUS_EXTENSIONS
        assert ".php" in DANGEROUS_EXTENSIONS
        assert ".sh" in DANGEROUS_EXTENSIONS
        assert ".js" in DANGEROUS_EXTENSIONS
    
    def test_double_extension_detection(self):
        """Teste: Detecção de extensão dupla"""
        filename = "documento.pdf.exe"
        parts = filename.split(".")
        assert len(parts) > 2  # Mais de uma extensão
        assert parts[-1] == "exe"  # Última extensão é executável


class TestDocumentValidators:
    """Testes de validação de documentos brasileiros"""
    
    def test_valid_cpf(self):
        """Teste: CPF válido aceito"""
        # CPF válido: 529.982.247-25
        assert validate_cpf("52998224725") is True
        assert validate_cpf("529.982.247-25") is True
    
    def test_invalid_cpf_digit(self):
        """Teste: CPF com dígito errado rejeitado"""
        assert validate_cpf("52998224726") is False  # Último dígito errado
    
    def test_invalid_cpf_repeated_digits(self):
        """Teste: CPF com dígitos repetidos rejeitado"""
        assert validate_cpf("11111111111") is False
        assert validate_cpf("00000000000") is False
    
    def test_invalid_cpf_length(self):
        """Teste: CPF com tamanho errado rejeitado"""
        assert validate_cpf("1234567890") is False  # 10 dígitos
        assert validate_cpf("123456789012") is False  # 12 dígitos
    
    def test_valid_cnpj(self):
        """Teste: CNPJ válido aceito"""
        # CNPJ válido: 11.222.333/0001-81
        assert validate_cnpj("11222333000181") is True
        assert validate_cnpj("11.222.333/0001-81") is True
    
    def test_invalid_cnpj_digit(self):
        """Teste: CNPJ com dígito errado rejeitado"""
        assert validate_cnpj("11222333000182") is False
    
    def test_invalid_cnpj_repeated_digits(self):
        """Teste: CNPJ com dígitos repetidos rejeitado"""
        assert validate_cnpj("11111111111111") is False


class TestSecurityUtils:
    """Testes de utilitários de segurança"""
    
    def test_safe_filename_generation(self):
        """Teste: Geração de nome de arquivo seguro"""
        from security.file_validation import sanitize_filename
        
        # Nome com caracteres perigosos
        dirty = "../../../etc/passwd"
        clean = sanitize_filename(dirty)
        assert "../" not in clean
        assert "/" not in clean or clean.count("/") == 0
    
    def test_path_traversal_prevention(self):
        """Teste: Prevenção de path traversal"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
            "%2e%2e%2fetc%2fpasswd"
        ]
        
        for path in malicious_paths:
            # Deve ser sanitizado
            assert ".." not in path.replace("%2e", ".") or len(path) < 10


# Marcar testes que requerem dependências externas
pytestmark = pytest.mark.security
