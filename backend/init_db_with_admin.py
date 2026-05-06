#!/usr/bin/env python
"""
Inicializa banco de dados e cria usuário admin padrão
"""

import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, SessionLocal, User
from security.auth import get_password_hash

def setup_database():
    print("🚀 Inicializando banco de dados...")
    
    # Criar tabelas
    init_db()
    
    # Criar usuário admin
    db = SessionLocal()
    try:
        # Verificar se admin já existe
        admin = db.query(User).filter(User.email == "admin@neobusiness.ai").first()
        
        if not admin:
            print(" Criando usuário admin...")
            admin = User(
                email="admin@neobusiness.ai",
                password_hash=get_password_hash("admin123"),
                name="Administrador",
                role="admin",
                plan_tier="enterprise",
                is_active=True
            )
            db.add(admin)
            
            # Criar usuários de teste
            test_users = [
                ("joao.silva@email.com", "Joao Silva", "user", "free"),
                ("maria.santos@empresa.com", "Maria Santos", "user", "premium"),
                ("ana.nova@gmail.com", "Ana Nova", "user", "free"),
            ]
            
            for email, name, role, plan in test_users:
                user = db.query(User).filter(User.email == email).first()
                if not user:
                    print(f"   Criando: {name} ({email})")
                    user = User(
                        email=email,
                        password_hash=get_password_hash("teste123"),
                        name=name,
                        role=role,
                        plan_tier=plan,
                        is_active=True
                    )
                    db.add(user)
            
            db.commit()
            print("✅ Usuários criados com sucesso!")
        else:
            print("✅ Usuário admin já existe")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n📋 Usuários disponíveis:")
    print("   admin@neobusiness.ai / admin123 (admin)")
    print("   joao.silva@email.com / teste123 (user)")
    print("   maria.santos@empresa.com / teste123 (premium)")
    print("   ana.nova@gmail.com / teste123 (user)")

if __name__ == "__main__":
    setup_database()
