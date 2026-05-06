"""
Script de Criação de Usuário Admin
==================================
Cria usuário administrador para testes.

Usage:
    python scripts/create_admin.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, User, Base, engine
from security.auth import get_password_hash, Role
from datetime import datetime

# Credenciais do Admin de Teste
ADMIN_EMAIL = "admin@neobusiness.ai"
ADMIN_PASSWORD = "Admin@123456!"
ADMIN_NAME = "Administrador NeoBusiness"

def create_admin_user():
    """Cria usuário administrador se não existir"""
    
    db = SessionLocal()
    
    try:
        # Verificar se já existe admin
        existing_admin = db.query(User).filter(
            User.email == ADMIN_EMAIL
        ).first()
        
        if existing_admin:
            print(f"✓ Administrador já existe: {ADMIN_EMAIL}")
            print(f"  ID: {existing_admin.id}")
            print(f"  Role: {existing_admin.role}")
            return
        
        # Criar hash da senha
        password_hash = get_password_hash(ADMIN_PASSWORD)
        
        # Criar usuário admin
        admin = User(
            email=ADMIN_EMAIL,
            password_hash=password_hash,
            name=ADMIN_NAME,
            role=Role.ADMIN.value,
            plan_tier="enterprise",
            subscription_status="active",
            documents_limit=1000,
            users_limit=100,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=None
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("=" * 60)
        print("✅ USUÁRIO ADMINISTRADOR CRIADO COM SUCESSO")
        print("=" * 60)
        print()
        print("📧 Email:", ADMIN_EMAIL)
        print("🔑 Senha:", ADMIN_PASSWORD)
        print("👤 Nome:", ADMIN_NAME)
        print("🎭 Role:", Role.ADMIN.value)
        print("📊 ID:", admin.id)
        print()
        print("=" * 60)
        print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro ao criar administrador: {e}")
        db.rollback()
    
    finally:
        db.close()


def create_test_users():
    """Cria usuários de teste adicionais"""
    
    db = SessionLocal()
    
    test_users = [
        {
            "email": "user@neobusiness.ai",
            "password": "User@123456!",
            "name": "Usuário Teste",
            "role": Role.USER.value,
            "plan_tier": "free"
        },
        {
            "email": "premium@neobusiness.ai",
            "password": "Premium@123456!",
            "name": "Usuário Premium",
            "role": Role.PREMIUM.value,
            "plan_tier": "premium"
        },
        {
            "email": "enterprise@neobusiness.ai",
            "password": "Enterprise@123456!",
            "name": "Usuário Enterprise",
            "role": Role.ENTERPRISE.value,
            "plan_tier": "enterprise"
        }
    ]
    
    try:
        for user_data in test_users:
            # Verificar se já existe
            existing = db.query(User).filter(
                User.email == user_data["email"]
            ).first()
            
            if existing:
                print(f"✓ Usuário já existe: {user_data['email']}")
                continue
            
            # Criar usuário
            password_hash = get_password_hash(user_data["password"])
            
            new_user = User(
                email=user_data["email"],
                password_hash=password_hash,
                name=user_data["name"],
                role=user_data["role"],
                plan_tier=user_data["plan_tier"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.add(new_user)
            print(f"✅ Criado: {user_data['email']} ({user_data['role']})")
        
        db.commit()
        print()
        print("=" * 60)
        print("✅ USUÁRIOS DE TESTE CRIADOS")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔐 NEOBUSINESS AI - CRIAÇÃO DE USUÁRIOS DE TESTE")
    print("=" * 60 + "\n")
    
    # Criar tabelas se não existirem
    Base.metadata.create_all(bind=engine)
    print("✓ Tabelas verificadas/criadas\n")
    
    # Criar admin
    create_admin_user()
    
    print("\n")
    
    # Criar usuários de teste
    create_test_users()
    
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETO!")
    print("=" * 60)
    print("\nVocê pode agora fazer login com:")
    print("  • Admin: admin@neobusiness.ai / Admin@123456!")
    print("  • User: user@neobusiness.ai / User@123456!")
    print("  • Premium: premium@neobusiness.ai / Premium@123456!")
    print("  • Enterprise: enterprise@neobusiness.ai / Enterprise@123456!")
    print("\n" + "=" * 60 + "\n")
