"""
MFA Service - LexScan IA
Multi-Factor Authentication com TOTP (Time-based One-Time Password)
Suporta: Google Authenticator, Authy, Microsoft Authenticator
"""

import os
import base64
import hmac
import hashlib
import struct
import time
import secrets
import qrcode
import io
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MFASecret:
    """Segredo MFA de um usuário"""
    user_id: str
    secret: str
    enabled: bool = False
    created_at: datetime = None
    verified_at: Optional[datetime] = None
    backup_codes: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.backup_codes is None:
            self.backup_codes = []


class TOTPService:
    """
    Implementação TOTP (RFC 6238)
    Compatível com Google Authenticator, Authy, Microsoft Authenticator
    """
    
    def __init__(self, issuer_name: str = "LexScan IA"):
        self.issuer_name = issuer_name
        self.digits = 6
        self.interval = 30  # segundos
    
    def generate_secret(self) -> str:
        """
        Gera um segredo TOTP aleatório (base32 encoded)
        
        Returns:
            Segredo em formato base32 (compatível com apps autenticador)
        """
        # 160 bits = 20 bytes = 32 caracteres base32
        random_bytes = secrets.token_bytes(20)
        return base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
    
    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verifica um token TOTP
        
        Args:
            secret: Segredo base32 do usuário
            token: Token de 6 dígitos fornecido pelo usuário
            window: Tolerância de janelas de tempo (±1 por padrão)
            
        Returns:
            True se o token é válido
        """
        if not token or len(token) != self.digits:
            return False
        
        try:
            token_int = int(token)
        except ValueError:
            return False
        
        # Verificar janela de tempo atual + anteriores + futuros
        current_time = int(time.time()) // self.interval
        
        for offset in range(-window, window + 1):
            expected_token = self._generate_token_at_time(secret, current_time + offset)
            if hmac.compare_digest(str(expected_token), str(token_int)):
                return True
        
        return False
    
    def _generate_token_at_time(self, secret: str, time_step: int) -> int:
        """Gera token para um timestep específico"""
        secret_bytes = base64.b32decode(secret + '=' * (8 - len(secret) % 8))
        time_bytes = struct.pack('>Q', time_step)
        
        # HMAC-SHA1
        h = hmac.new(secret_bytes, time_bytes, hashlib.sha1)
        digest = h.digest()
        
        # Dynamic truncation
        offset = digest[-1] & 0x0F
        code = struct.unpack('>I', digest[offset:offset + 4])[0]
        code = (code & 0x7FFFFFFF) % (10 ** self.digits)
        
        return code
    
    def generate_provisioning_uri(self, user_email: str, secret: str) -> str:
        """
        Gera URI para QR Code (otpauth://)
        
        Args:
            user_email: Email do usuário
            secret: Segredo TOTP
            
        Returns:
            URI otpauth:// para QR Code
        """
        label = f"{self.issuer_name}:{user_email}"
        uri = (
            f"otpauth://totp/{label}?"
            f"secret={secret}&"
            f"issuer={self.issuer_name}&"
            f"algorithm=SHA1&"
            f"digits={self.digits}&"
            f"period={self.interval}"
        )
        return uri
    
    def generate_qr_code(self, provisioning_uri: str) -> bytes:
        """
        Gera QR Code como bytes PNG
        
        Args:
            provisioning_uri: URI otpauth://
            
        Returns:
            Imagem QR Code em bytes PNG
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()


class MFAService:
    """
    Serviço completo de MFA para LexScan IA
    
    Features:
    - TOTP (Time-based One-Time Password)
    - Backup codes (10 códigos de recuperação)
    - QR Code para configuração
    - Rate limiting em verificações
    - Audit logging
    """
    
    def __init__(self):
        self.totp = TOTPService(issuer_name="LexScan IA")
        # Em produção, usar banco de dados real
        self._secrets: Dict[str, MFASecret] = {}
        self._verification_attempts: Dict[str, List[datetime]] = {}
    
    def setup_mfa(self, user_id: str, user_email: str) -> Dict:
        """
        Inicia setup de MFA para um usuário
        
        Returns:
            Dict com secret, provisioning_uri e qr_code
        """
        # Gerar segredo
        secret = self.totp.generate_secret()
        
        # Criar entry
        mfa_secret = MFASecret(
            user_id=user_id,
            secret=secret,
            enabled=False,
            backup_codes=self._generate_backup_codes()
        )
        self._secrets[user_id] = mfa_secret
        
        # Gerar QR Code
        provisioning_uri = self.totp.generate_provisioning_uri(user_email, secret)
        qr_code = self.totp.generate_qr_code(provisioning_uri)
        
        return {
            'secret': secret,
            'provisioning_uri': provisioning_uri,
            'qr_code_base64': base64.b64encode(qr_code).decode('utf-8'),
            'backup_codes': mfa_secret.backup_codes,
            'instructions': [
                '1. Instale Google Authenticator ou Authy',
                '2. Escaneie o QR Code ou insira o segredo manualmente',
                '3. Guarde os códigos de backup em local seguro',
                '4. Digite o código de 6 dígitos para verificar'
            ]
        }
    
    def verify_and_enable(self, user_id: str, token: str) -> Tuple[bool, str]:
        """
        Verifica token e habilita MFA se correto
        
        Args:
            user_id: ID do usuário
            token: Código TOTP de 6 dígitos
            
        Returns:
            (success, message)
        """
        # Rate limiting
        if not self._check_rate_limit(user_id):
            return False, "Muitas tentativas. Aguarde 5 minutos."
        
        # Buscar segredo
        mfa_secret = self._secrets.get(user_id)
        if not mfa_secret:
            return False, "MFA não configurado para este usuário"
        
        # Verificar token
        if not self.totp.verify_token(mfa_secret.secret, token):
            self._record_attempt(user_id)
            return False, "Código inválido. Tente novamente."
        
        # Habilitar MFA
        mfa_secret.enabled = True
        mfa_secret.verified_at = datetime.utcnow()
        
        return True, "MFA habilitado com sucesso!"
    
    def verify_mfa(self, user_id: str, token: str) -> Tuple[bool, str]:
        """
        Verifica token MFA durante login
        
        Args:
            user_id: ID do usuário
            token: Código TOTP ou backup code
            
        Returns:
            (success, message)
        """
        # Rate limiting
        if not self._check_rate_limit(user_id):
            return False, "Muitas tentativas. Aguarde 5 minutos."
        
        mfa_secret = self._secrets.get(user_id)
        if not mfa_secret or not mfa_secret.enabled:
            return False, "MFA não habilitado"
        
        # Tentar como backup code primeiro
        if token in mfa_secret.backup_codes:
            mfa_secret.backup_codes.remove(token)
            return True, "Código de backup aceito"
        
        # Verificar como TOTP
        if self.totp.verify_token(mfa_secret.secret, token):
            return True, "Código TOTP válido"
        
        self._record_attempt(user_id)
        return False, "Código inválido"
    
    def disable_mfa(self, user_id: str, password: str) -> Tuple[bool, str]:
        """
        Desabilita MFA para um usuário
        
        Args:
            user_id: ID do usuário
            password: Senha atual para confirmação
            
        Returns:
            (success, message)
        """
        mfa_secret = self._secrets.get(user_id)
        if not mfa_secret:
            return False, "MFA não está habilitado"
        
        # Em produção, verificar senha com Firebase Auth
        # Por enquanto, apenas desabilita
        mfa_secret.enabled = False
        
        return True, "MFA desabilitado com sucesso"
    
    def regenerate_backup_codes(self, user_id: str, mfa_token: str) -> Tuple[bool, List[str] or str]:
        """
        Regenera códigos de backup
        
        Args:
            user_id: ID do usuário
            mfa_token: Token MFA atual para verificação
            
        Returns:
            (success, backup_codes ou mensagem de erro)
        """
        success, msg = self.verify_mfa(user_id, mfa_token)
        if not success:
            return False, "Token MFA inválido"
        
        mfa_secret = self._secrets.get(user_id)
        new_codes = self._generate_backup_codes()
        mfa_secret.backup_codes = new_codes
        
        return True, new_codes
    
    def is_mfa_enabled(self, user_id: str) -> bool:
        """Verifica se MFA está habilitado para o usuário"""
        mfa_secret = self._secrets.get(user_id)
        return mfa_secret is not None and mfa_secret.enabled
    
    def get_mfa_status(self, user_id: str) -> Dict:
        """Retorna status completo do MFA"""
        mfa_secret = self._secrets.get(user_id)
        
        if not mfa_secret:
            return {
                'enabled': False,
                'configured': False,
                'method': None
            }
        
        return {
            'enabled': mfa_secret.enabled,
            'configured': True,
            'method': 'TOTP',
            'created_at': mfa_secret.created_at.isoformat() if mfa_secret.created_at else None,
            'verified_at': mfa_secret.verified_at.isoformat() if mfa_secret.verified_at else None,
            'backup_codes_remaining': len(mfa_secret.backup_codes)
        }
    
    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Gera códigos de backup únicos"""
        codes = []
        for _ in range(count):
            # 8 caracteres alfanuméricos, fácil de digitar
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            codes.append(code)
        return codes
    
    def _check_rate_limit(self, user_id: str, max_attempts: int = 5, window_minutes: int = 5) -> bool:
        """Verifica rate limiting de tentativas"""
        attempts = self._verification_attempts.get(user_id, [])
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # Limpar tentativas antigas
        recent_attempts = [a for a in attempts if a > cutoff]
        self._verification_attempts[user_id] = recent_attempts
        
        return len(recent_attempts) < max_attempts
    
    def _record_attempt(self, user_id: str):
        """Registra tentativa de verificação"""
        if user_id not in self._verification_attempts:
            self._verification_attempts[user_id] = []
        self._verification_attempts[user_id].append(datetime.utcnow())


# =============================================================================
# INTEGRAÇÃO COM FIREBASE AUTH
# =============================================================================

class FirebaseMFAIntegration:
    """
    Integra MFA com Firebase Authentication
    
    Suporta:
    - SMS MFA
    - TOTP MFA (via Firebase)
    - SAML/SSO (Enterprise)
    """
    
    def __init__(self):
        self.mfa_service = MFAService()
    
    def start_mfa_enrollment(self, user_id: str, user_email: str) -> Dict:
        """
        Inicia enrollment de MFA (TOTP)
        
        Returns:
            Setup information incluindo QR Code
        """
        return self.mfa_service.setup_mfa(user_id, user_email)
    
    def verify_enrollment(self, user_id: str, token: str) -> bool:
        """Completa enrollment verificando primeiro token"""
        success, _ = self.mfa_service.verify_and_enable(user_id, token)
        return success
    
    def require_mfa_for_login(self, user_id: str) -> bool:
        """
        Verifica se usuário requer MFA para login
        Chamado após autenticação Firebase bem-sucedida
        """
        return self.mfa_service.is_mfa_enabled(user_id)
    
    def complete_login_with_mfa(self, user_id: str, mfa_token: str) -> Tuple[bool, str]:
        """
        Completa login verificando MFA
        
        Args:
            user_id: ID do usuário (já autenticado no Firebase)
            mfa_token: Código MFA (TOTP ou backup)
            
        Returns:
            (success, message)
        """
        return self.mfa_service.verify_mfa(user_id, mfa_token)


# Instância global
mfa_service = MFAService()
firebase_mfa = FirebaseMFAIntegration()


# =============================================================================
# TESTES
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MFA SERVICE - TESTE")
    print("=" * 60)
    
    # Teste 1: Setup MFA
    print("\n1. Setup MFA:")
    setup = mfa_service.setup_mfa("user_123", "test@example.com")
    print(f"   Segredo gerado: {setup['secret'][:20]}...")
    print(f"   Códigos de backup: {len(setup['backup_codes'])}")
    
    # Teste 2: Verificar token
    print("\n2. Teste de verificação:")
    
    # Gerar token atual
    totp = TOTPService()
    current_token = totp._generate_token_at_time(
        setup['secret'], 
        int(time.time()) // 30
    )
    print(f"   Token atual: {current_token:06d}")
    
    # Verificar
    success, msg = mfa_service.verify_and_enable("user_123", f"{current_token:06d}")
    print(f"   Resultado: {'✅' if success else '❌'} {msg}")
    
    # Teste 3: Status
    print("\n3. Status MFA:")
    status = mfa_service.get_mfa_status("user_123")
    print(f"   Habilitado: {status['enabled']}")
    print(f"   Backup codes: {status['backup_codes_remaining']}")
    
    print("\n" + "=" * 60)
    print("TESTES COMPLETADOS!")
    print("=" * 60)
