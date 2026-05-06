#!/usr/bin/env python
"""
Simulação de Login - Teste com usuário admin
Testa: admin@neobusiness.ai / Admin@123456!
"""

import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"

# Usuário de teste fornecido
TEST_USER = {
    "email": "admin@neobusiness.ai",
    "password": "admin123"
}

async def test_login():
    """Testa login do usuário admin"""
    print("="*60)
    print("🧪 SIMULAÇÃO DE LOGIN - NeoBusiness AI")
    print("="*60)
    print(f"\n👤 Testando: {TEST_USER['email']}")
    
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            # Teste de login
            print("\n📤 Enviando POST /auth/login...")
            response = await client.post("/auth/login", json=TEST_USER)
            
            print(f"📥 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ LOGIN SUCESSO!")
                print(f"   Token: {data.get('access_token', 'N/A')[:40]}...")
                print(f"   Tipo: {data.get('token_type', 'N/A')}")
                
                if 'user' in data:
                    user = data['user']
                    print(f"   Usuário: {user.get('name', 'N/A')} ({user.get('email', 'N/A')})")
                    print(f"   Role: {user.get('role', 'N/A')}")
                    print(f"   Plano: {user.get('plan_tier', 'N/A')}")
                
                return True
            elif response.status_code == 401:
                print(f"❌ LOGIN FALHOU - Credenciais inválidas")
                print(f"   Resposta: {response.text}")
                return False
            else:
                print(f"❌ ERRO {response.status_code}")
                print(f"   Resposta: {response.text[:500]}")
                return False
                
    except httpx.ConnectError:
        print(f"❌ ERRO: Não consegui conectar ao backend em {BASE_URL}")
        print(f"   Verifique se o servidor está rodando!")
        return False
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando simulação de login...")
    print(f"Backend: {BASE_URL}")
    print()
    
    success = asyncio.run(test_login())
    
    print("\n" + "="*60)
    if success:
        print("✅ TESTE PASSOU - Login funcionando!")
    else:
        print("❌ TESTE FALHOU - Login não funcionou")
    print("="*60)
    
    sys.exit(0 if success else 1)
