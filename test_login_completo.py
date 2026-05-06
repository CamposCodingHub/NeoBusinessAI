#!/usr/bin/env python
"""
Teste Completo de Login - NeoBusiness AI
Testa todos os usuários simulados
"""

import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000"

# Usuários de teste criados na simulação
TEST_USERS = [
    {"email": "joao.silva@email.com", "password": "Teste123!", "type": "comum", "name": "João Silva"},
    {"email": "maria.santos@empresa.com", "password": "Teste123!", "type": "premium", "name": "Maria Santos"},
    {"email": "admin@neobusiness.ai", "password": "Teste123!", "type": "admin", "name": "Carlos Admin"},
    {"email": "ana.nova@gmail.com", "password": "Teste123!", "type": "novo", "name": "Ana Nova"},
]

async def test_register_and_login():
    """Testa registro e login de todos os usuários"""
    print("="*60)
    print("🧪 TESTE COMPLETO DE LOGIN - NeoBusiness AI")
    print("="*60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        for user in TEST_USERS:
            print(f"\n👤 Testando usuário: {user['name']} ({user['type']})")
            print(f"   Email: {user['email']}")
            
            # 1. Tentar registro
            try:
                register_data = {
                    "email": user['email'],
                    "password": user['password'],
                    "name": user['name']
                }
                
                response = await client.post("/auth/register", json=register_data)
                
                if response.status_code == 201 or response.status_code == 200:
                    print(f"   ✅ Registro: SUCESSO")
                    data = response.json()
                    print(f"      Token: {data.get('access_token', 'N/A')[:30]}...")
                elif response.status_code == 400 and "já registrado" in response.text:
                    print(f"   ⚠️  Registro: Usuário já existe (OK)")
                else:
                    print(f"   ❌ Registro: FALHA - {response.status_code}")
                    print(f"      {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Erro no registro: {e}")
            
            # 2. Testar login
            try:
                login_data = {
                    "email": user['email'],
                    "password": user['password']
                }
                
                response = await client.post("/auth/login", json=login_data)
                
                if response.status_code == 200:
                    print(f"   ✅ Login: SUCESSO")
                    data = response.json()
                    token = data.get('access_token', 'N/A')
                    print(f"      Token: {token[:30]}...")
                    
                    # 3. Testar acesso a recurso protegido
                    headers = {"Authorization": f"Bearer {token}"}
                    me_response = await client.get("/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        print(f"   ✅ Acesso protegido: OK")
                    else:
                        print(f"   ⚠️  Acesso protegido: {me_response.status_code}")
                        
                elif response.status_code == 401:
                    print(f"   ❌ Login: CREDENCIAIS INVÁLIDAS")
                else:
                    print(f"   ❌ Login: ERRO {response.status_code}")
                    print(f"      {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Erro no login: {e}")
                import traceback
                traceback.print_exc()
        
        # Teste de login inválido
        print(f"\n🚨 Testando login inválido (segurança):")
        try:
            invalid_login = {
                "email": "naoexiste@email.com",
                "password": "senhaerrada123"
            }
            response = await client.post("/auth/login", json=invalid_login)
            
            if response.status_code == 401:
                print(f"   ✅ Acesso negado corretamente (401)")
            else:
                print(f"   ⚠️  Resposta inesperada: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS!")
    print("="*60)

if __name__ == "__main__":
    print("🚀 Iniciando testes de login...")
    print(f"Backend: {BASE_URL}")
    print("Certifique-se de que o backend está rodando!")
    print()
    
    try:
        asyncio.run(test_register_and_login())
    except KeyboardInterrupt:
        print("\n⚠️  Teste interrompido")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
