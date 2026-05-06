"""
Script de Teste de Autenticação
================================
Testa rapidamente se o sistema de auth está funcionando.

Usage:
    python scripts/test_auth.py
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

# Credenciais de teste
TEST_USERS = [
    {"email": "admin@neobusiness.ai", "password": "Admin@123456!", "role": "admin"},
    {"email": "user@neobusiness.ai", "password": "User@123456!", "role": "user"},
    {"email": "premium@neobusiness.ai", "password": "Premium@123456!", "role": "premium"},
]

def test_login(email, password, expected_role):
    """Testa login de usuário"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            role = data.get("user", {}).get("role")
            
            print(f"✅ {email} - Login OK (Role: {role})")
            
            if role == expected_role:
                print(f"   └─ Role correto: {role}")
            else:
                print(f"   ⚠️  Role incorreto: esperado {expected_role}, obtido {role}")
            
            return token
        else:
            print(f"❌ {email} - Erro: {response.status_code}")
            print(f"   └─ {response.text[:100]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {email} - Servidor não está rodando")
        return None
    except Exception as e:
        print(f"❌ {email} - Erro: {e}")
        return None

def test_protected_endpoint(token):
    """Testa acesso a endpoint protegido"""
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   └─ /auth/me OK: {data.get('name')} ({data.get('email')})")
            return True
        else:
            print(f"   ❌ /auth/me falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_admin_endpoint(token):
    """Testa acesso a endpoint admin"""
    try:
        response = requests.get(
            f"{BASE_URL}/auth/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            users = response.json()
            print(f"   └─ /admin/users OK: {len(users)} usuários encontrados")
            return True
        elif response.status_code == 403:
            print(f"   ⚠️  /admin/users - Acesso negado (Role não é admin)")
            return False
        else:
            print(f"   ❌ /admin/users falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🧪 TESTE DE AUTENTICAÇÃO - NEOBUSINESS AI")
    print("=" * 60 + "\n")
    
    print(f"Base URL: {BASE_URL}\n")
    
    results = []
    
    for user in TEST_USERS:
        print(f"\n🔐 Testando: {user['email']}")
        print("-" * 40)
        
        # Testar login
        token = test_login(user["email"], user["password"], user["role"])
        
        if token:
            # Testar endpoint protegido
            me_ok = test_protected_endpoint(token)
            
            # Testar endpoint admin
            admin_ok = test_admin_endpoint(token)
            
            results.append({
                "email": user["email"],
                "login": True,
                "me": me_ok,
                "admin": admin_ok if user["role"] == "admin" else None
            })
        else:
            results.append({
                "email": user["email"],
                "login": False,
                "me": False,
                "admin": None
            })
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60 + "\n")
    
    for r in results:
        status = "✅" if r["login"] and r["me"] else "❌"
        print(f"{status} {r['email']}")
        print(f"   Login: {'✅' if r['login'] else '❌'}")
        print(f"   /auth/me: {'✅' if r['me'] else '❌'}")
        if r["admin"] is not None:
            print(f"   /admin/users: {'✅' if r['admin'] else '❌'}")
    
    print("\n" + "=" * 60)
    
    # Verificar se todos passaram
    all_passed = all(r["login"] and r["me"] for r in results)
    
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("=" * 60 + "\n")
        return 0
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        print("=" * 60 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
