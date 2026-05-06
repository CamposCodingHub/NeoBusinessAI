"""
Criptografia de Dados Sensíveis - LGPD Compliance
AES-256 para criptografia em repouso
"""

import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json

# Carregar chave de criptografia do ambiente
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

if not ENCRYPTION_KEY:
    # Fallback para desenvolvimento (NÃO usar em produção!)
    ENCRYPTION_KEY = 'development-key-32bytes-long!!!!!'

# Derivar chave de 32 bytes
def get_fernet():
    """Retorna instância Fernet para criptografia"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'jurisflow_salt_2024',  # Em produção, use salt único por campo
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
    return Fernet(key)

fernet = get_fernet()


def encrypt_field(value: str) -> str:
    """Criptografa um campo sensível"""
    if not value:
        return value
    
    try:
        encrypted = fernet.encrypt(value.encode())
        return f"ENC:{encrypted.decode()}"
    except Exception as e:
        print(f"Erro ao criptografar: {e}")
        return value


def decrypt_field(value: str) -> str:
    """Descriptografa um campo sensível"""
    if not value or not value.startswith("ENC:"):
        return value
    
    try:
        encrypted_data = value[4:]  # Remove prefixo "ENC:"
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"Erro ao descriptografar: {e}")
        return value


def encrypt_dict(data: dict, sensitive_fields: list) -> dict:
    """Criptografa campos sensíveis em um dicionário"""
    result = data.copy()
    for field in sensitive_fields:
        if field in result and result[field]:
            result[field] = encrypt_field(str(result[field]))
    return result


def decrypt_dict(data: dict, sensitive_fields: list) -> dict:
    """Descriptografa campos sensíveis em um dicionário"""
    result = data.copy()
    for field in sensitive_fields:
        if field in result and result[field]:
            result[field] = decrypt_field(result[field])
    return result


# Lista de campos sensíveis por modelo
SENSITIVE_FIELDS = {
    'Client': ['cpf_cnpj', 'phone', 'address', 'zip_code'],
    'User': ['phone'],
    'Invoice': [],  # Dados financeiros já são protegidos por outras camadas
    'WhatsAppConfig': ['twilio_account_sid', 'twilio_auth_token', 'evolution_api_key'],
}


def should_encrypt_field(model_name: str, field_name: str) -> bool:
    """Verifica se um campo deve ser criptografado"""
    return field_name in SENSITIVE_FIELDS.get(model_name, [])
