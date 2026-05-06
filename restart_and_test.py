#!/usr/bin/env python
"""
Reinicia o servidor e testa o login automaticamente
"""

import subprocess
import time
import sys
import signal
import os

def main():
    print("🚀 Reiniciando servidor e testando login...")
    print("="*60)
    
    # 1. Matar processos uvicorn existentes
    print("\n1. Limpando processos antigos...")
    try:
        subprocess.run("taskkill /F /IM python.exe 2>nul", shell=True, capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # 2. Iniciar servidor em background
    print("\n2. Iniciando servidor backend...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd="backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Aguardar servidor iniciar
    print("   Aguardando servidor iniciar (10s)...")
    time.sleep(10)
    
    # 3. Testar login
    print("\n3. Testando login...")
    try:
        import httpx
        import asyncio
        
        async def test_login():
            async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
                # Teste 1: Login usuário existente
                print("   Testando: joao.silva@email.com")
                response = await client.post("/auth/login", json={
                    "email": "joao.silva@email.com",
                    "password": "Teste123!"
                })
                
                if response.status_code == 200:
                    print(f"   ✅ Login OK - {response.status_code}")
                    return True
                else:
                    print(f"   ❌ Login falhou - {response.status_code}")
                    print(f"      {response.text[:200]}")
                    return False
        
        result = asyncio.run(test_login())
        
        if result:
            print("\n" + "="*60)
            print("✅ SERVIDOR FUNCIONANDO!")
            print("="*60)
            print("\nServidor rodando em: http://localhost:8000")
            print("Docs: http://localhost:8000/docs")
            print("\nPressione CTRL+C para parar")
            
            # Manter servidor rodando
            try:
                while True:
                    output = server_process.stdout.readline()
                    if output:
                        print(output.strip())
            except KeyboardInterrupt:
                print("\n\n🛑 Parando servidor...")
                server_process.terminate()
        else:
            print("\n❌ Falha no teste de login")
            server_process.terminate()
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        server_process.terminate()

if __name__ == "__main__":
    main()
