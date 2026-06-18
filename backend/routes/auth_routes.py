"""
Rotas de Autenticação
=====================
Login, registro, refresh token e gestão de usuários.
"""

import os
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db_async, User
from security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    require_role,
    Role,
    get_password_hash,
    verify_password,
    validate_schema,
    UserCreateSchema,
    UserLoginSchema,
    rate_limit,
    LOGIN_RATE_LIMIT,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticação"])
security = HTTPBearer()


@router.post("/register", response_model=dict)
@rate_limit(requests_per_minute=5)
async def register(
    user_data: UserCreateSchema,
    db: Session = Depends(get_db_async),
):
    """
    Registra novo usuário.

    - email: Email válido e único
    - password: Senha forte
    - name: Nome completo
    """

    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado",
        )

    password_hash = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        password_hash=password_hash,
        name=user_data.name,
        role=Role.USER.value,
        plan_tier="free",
        is_active=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"Novo usuário registrado: {user_data.email}")

    access_token = create_access_token(
        user_id=str(new_user.id),
        role=Role.USER,
    )

    refresh_token = create_refresh_token(
        user_id=str(new_user.id),
    )

    return {
        "message": "Usuário registrado com sucesso",
        "user_id": new_user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=dict)
@rate_limit(requests_per_minute=LOGIN_RATE_LIMIT.requests_per_minute)
async def login(
    credentials: UserLoginSchema,
    db: Session = Depends(get_db_async),
):
    """
    Autentica usuário e retorna tokens JWT.

    - email: Email registrado
    - password: Senha
    """

    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Tentativa de login falhou: {credentials.email}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    user.last_login = datetime.utcnow()
    db.commit()

    try:
        user_role = Role(user.role)
    except ValueError:
        user_role = Role.USER

    access_token = create_access_token(
        user_id=str(user.id),
        role=user_role,
    )

    refresh_token = create_refresh_token(
        user_id=str(user.id),
    )

    logger.info(f"Login bem-sucedido: {user.email} (Role: {user_role.value})")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user_role.value,
            "plan_tier": user.plan_tier,
        },
    }


# ==================== PASSWORD RECOVERY ====================


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    email: str,
    db: Session = Depends(get_db_async),
):
    """
    Solicita recuperação de senha.
    Envia email com link para reset.
    """

    user = db.query(User).filter(User.email == email).first()

    # Sempre retornar sucesso, mesmo se o email não existir.
    # Isso evita que alguém descubra quais emails estão cadastrados.
    if not user:
        logger.info(f"Tentativa de recuperação para email inexistente: {email}")

        return {
            "message": "Se o email estiver cadastrado, você receberá instruções de recuperação"
        }

    reset_token = create_access_token(
        user_id=str(user.id),
        expires_delta=timedelta(hours=1),
    )

    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"

    logger.info(f"Token de recuperação gerado para {email}: {reset_link}")

    return {
        "message": "Se o email estiver cadastrado, você receberá instruções de recuperação",
        "debug_link": reset_link if os.getenv("DEBUG") == "true" else None,
    }


@router.post("/reset-password", response_model=dict)
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db_async),
):
    """
    Redefine senha usando token de recuperação.
    """

    try:
        payload = verify_token(token, token_type="access")
        user_id = int(payload["sub"])

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )

        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha deve ter no mínimo 8 caracteres",
            )

        user.password_hash = get_password_hash(new_password)
        db.commit()

        logger.info(f"Senha redefinida para: {user.email}")

        return {
            "message": "Senha redefinida com sucesso",
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Erro ao redefinir senha: {e}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado",
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Renova access token usando refresh token.
    """

    try:
        payload = verify_token(
            credentials.credentials,
            token_type="refresh",
        )

        user_id = payload["sub"]

        new_access_token = create_access_token(
            user_id=user_id,
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    except Exception as e:
        logger.error(f"Erro ao renovar token: {e}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )


@router.get("/me", response_model=dict)
async def get_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db_async),
):
    """
    Retorna informações do usuário logado.
    """

    user = db.query(User).filter(User.id == int(current_user.user_id)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "plan_tier": user.plan_tier,
        "subscription_status": user.subscription_status,
        "documents_limit": user.documents_limit,
        "users_limit": user.users_limit,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    current_user=Depends(get_current_user),
):
    """
    Logout - invalida token no servidor usando blacklist.
    """

    from security.token_blacklist import blacklist_token

    auth_header = request.headers.get("Authorization", "")

    token_invalidated = False

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        blacklist_token(
            token,
            expires_in=3600,
        )

        token_invalidated = True

        logger.info(f"Token adicionado à blacklist: {current_user.user_id}")

    logger.info(f"Logout realizado: {current_user.user_id}")

    return {
        "message": "Logout realizado com sucesso",
        "token_invalidated": token_invalidated,
    }


# ==================== ADMIN ROUTES ====================


@router.get("/admin/users", response_model=list)
async def list_all_users(
    admin_user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db_async),
):
    """
    Lista todos os usuários.
    Apenas administradores podem acessar.
    """

    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "plan_tier": user.plan_tier,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in users
    ]


@router.post("/admin/create-admin", response_model=dict)
async def create_admin_user(
    user_data: UserCreateSchema,
    admin_user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db_async),
):
    """
    Cria usuário administrador.
    Apenas um administrador existente pode criar outro administrador.
    """

    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já registrado",
        )

    password_hash = get_password_hash(user_data.password)

    new_admin = User(
        email=user_data.email,
        password_hash=password_hash,
        name=user_data.name,
        role=Role.ADMIN.value,
        plan_tier="enterprise",
        is_active=True,
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    logger.warning(
        f"Novo admin criado por {admin_user.user_id}: {user_data.email}"
    )

    return {
        "message": "Administrador criado com sucesso",
        "user_id": new_admin.id,
        "email": new_admin.email,
        "role": Role.ADMIN.value,
    }


@router.patch("/admin/users/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: int,
    new_role: Role,
    admin_user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db_async),
):
    """
    Atualiza papel de usuário.
    Apenas administradores podem acessar.
    """

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    old_role = user.role
    user.role = new_role.value

    db.commit()

    logger.warning(
        f"Role alterado por admin {admin_user.user_id}: "
        f"User {user_id} {old_role} -> {new_role.value}"
    )

    return {
        "message": "Papel atualizado",
        "user_id": user_id,
        "new_role": new_role.value,
    }