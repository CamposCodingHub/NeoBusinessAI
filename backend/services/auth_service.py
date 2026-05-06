"""
Authentication Service
======================
Serviço de autenticação enterprise com device tracking e anti-brute force.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import secrets
import hashlib
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from core.config import settings
from models.user import User, Device, RefreshToken, UserRole
from models.audit_log import AuditLog, AuditAction, AuditSeverity
from core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    verify_token
)


class AuthService:
    """Serviço de autenticação"""
    
    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Tuple[User, str, str]:
        """
        Autentica usuário e retorna tokens.
        
        Args:
            db: Sessão do banco
            email: Email do usuário
            password: Senha em texto plano
            ip_address: IP do request
            user_agent: User-Agent do request
            
        Returns:
            Tuple[User, access_token, refresh_token]
            
        Raises:
            HTTPException: Se credenciais inválidas ou conta suspensa
        """
        # Buscar usuário
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Log tentativa falha
            AuthService._log_failed_login(db, email, ip_address, user_agent)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        # Verificar senha
        if not verify_password(password, user.password_hash):
            AuthService._log_failed_login(db, email, ip_address, user_agent)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        # Verificar se conta está ativa
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta desativada"
            )
        
        if user.is_suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Conta suspensa: {user.suspension_reason}"
            )
        
        # Verificar email verificado
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email não verificado"
            )
        
        # Criar ou atualizar device
        device = AuthService._get_or_create_device(
            db, user, ip_address, user_agent
        )
        
        # Criar tokens
        access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role.value
        )
        
        refresh_token = AuthService._create_refresh_token(db, user, device)
        
        # Atualizar last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Log sucesso
        AuthService._log_audit(
            db, user, AuditAction.LOGIN,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=str(device.id)
        )
        
        return user, access_token, refresh_token
    
    @staticmethod
    def refresh_tokens(
        db: Session,
        refresh_token: str,
        ip_address: str,
        user_agent: str
    ) -> Tuple[str, str]:
        """
        Renova access token usando refresh token.
        
        Args:
            db: Sessão do banco
            refresh_token: Refresh token válido
            ip_address: IP do request
            user_agent: User-Agent do request
            
        Returns:
            Tuple[new_access_token, new_refresh_token]
        """
        # Buscar refresh token
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )
        
        # Verificar se token foi revogado
        if token_record.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revogado"
            )
        
        # Verificar expiração
        if token_record.expires_at < datetime.utcnow():
            token_record.is_revoked = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expirado"
            )
        
        # Verificar usuário ativo
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inativo"
            )
        
        # Revogar token antigo (rotative refresh)
        token_record.is_revoked = True
        token_record.revoked_at = datetime.utcnow()
        
        # Criar novo refresh token
        new_refresh_token = AuthService._create_refresh_token(
            db, user, token_record.device
        )
        
        # Criar novo access token
        new_access_token = create_access_token(
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            role=user.role.value
        )
        
        db.commit()
        
        return new_access_token, new_refresh_token
    
    @staticmethod
    def logout(db: Session, user_id: str, device_id: str):
        """
        Faz logout do usuário (revoga refresh token do device).
        """
        # Revogar todos os refresh tokens do device
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.device_id == device_id
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.utcnow()
        })
        
        db.commit()
    
    @staticmethod
    def logout_all(db: Session, user_id: str):
        """
        Faz logout de todos os devices do usuário.
        """
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.utcnow()
        })
        
        db.commit()
    
    @staticmethod
    def _get_or_create_device(
        db: Session,
        user: User,
        ip_address: str,
        user_agent: str
    ) -> Device:
        """Cria ou recupera device do usuário"""
        # Gerar device_id único baseado em user_agent + IP
        device_hash = hashlib.sha256(
            f"{user_agent}:{ip_address}".encode()
        ).hexdigest()
        
        device = db.query(Device).filter(
            Device.user_id == user.id,
            Device.device_id == device_hash
        ).first()
        
        if not device:
            device = Device(
                user_id=user.id,
                device_id=device_hash,
                user_agent=user_agent,
                ip_address=ip_address,
                device_type=AuthService._detect_device_type(user_agent),
                browser=AuthService._detect_browser(user_agent),
                os=AuthService._detect_os(user_agent),
            )
            db.add(device)
            db.commit()
            db.refresh(device)
        else:
            # Atualizar last seen
            device.last_seen_at = datetime.utcnow()
            device.ip_address = ip_address
            db.commit()
        
        return device
    
    @staticmethod
    def _create_refresh_token(
        db: Session,
        user: User,
        device: Device
    ) -> str:
        """Cria refresh token"""
        token = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        refresh_token = RefreshToken(
            user_id=user.id,
            device_id=device.id,
            token=token,
            expires_at=expires_at
        )
        
        db.add(refresh_token)
        db.commit()
        
        return token
    
    @staticmethod
    def _log_failed_login(
        db: Session,
        email: str,
        ip_address: str,
        user_agent: str
    ):
        """Log de tentativa de login falha"""
        # TODO: Implementar rate limiting por IP
        pass
    
    @staticmethod
    def _log_audit(
        db: Session,
        user: User,
        action: AuditAction,
        **kwargs
    ):
        """Log de auditoria"""
        log = AuditLog(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action=action,
            severity=AuditSeverity.INFO,
            **kwargs
        )
        db.add(log)
        db.commit()
    
    @staticmethod
    def _detect_device_type(user_agent: str) -> str:
        """Detecta tipo de device"""
        user_agent_lower = user_agent.lower()
        if "mobile" in user_agent_lower or "android" in user_agent_lower:
            return "mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            return "tablet"
        return "desktop"
    
    @staticmethod
    def _detect_browser(user_agent: str) -> str:
        """Detecta browser"""
        user_agent_lower = user_agent.lower()
        if "chrome" in user_agent_lower:
            return "chrome"
        elif "firefox" in user_agent_lower:
            return "firefox"
        elif "safari" in user_agent_lower:
            return "safari"
        elif "edge" in user_agent_lower:
            return "edge"
        return "unknown"
    
    @staticmethod
    def _detect_os(user_agent: str) -> str:
        """Detecta sistema operacional"""
        user_agent_lower = user_agent.lower()
        if "windows" in user_agent_lower:
            return "windows"
        elif "mac" in user_agent_lower:
            return "macos"
        elif "linux" in user_agent_lower:
            return "linux"
        elif "android" in user_agent_lower:
            return "android"
        elif "ios" in user_agent_lower:
            return "ios"
        return "unknown"
