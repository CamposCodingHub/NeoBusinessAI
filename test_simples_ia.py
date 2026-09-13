"""
Teste Simplificado da IA do NeoBusinessAI
Testa os componentes basicos sem dependencias complexas
"""

import sys
import os
import subprocess

# Usar o venv do backend
venv_python = os.path.join(os.path.dirname(__file__), 'backend', 'venv311', 'Scripts', 'python.exe')

print("=" * 60)
print("TESTE SIMPLIFICADO - NeoBusinessAI")
print("=" * 60)

# Teste 1: Configuracao
print("\n[1/5] Testando configuracao...")
try:
    result = subprocess.run(
        [venv_python, "-c", "from config import settings; print('OK:', settings.ENVIRONMENT)"],
        cwd=os.path.join(os.path.dirname(__file__), 'backend'),
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode == 0:
        print("[OK] Configuracao carregada")
        print(f"   Output: {result.stdout.strip()}")
    else:
        print("[ERRO] Erro na configuracao")
        print(f"   Stderr: {result.stderr}")
except Exception as e:
    print(f"[ERRO] Excecao: {e}")

# Teste 2: Importar modulos IA
print("\n[2/5] Testando importacao de modulos IA...")
modules_to_test = [
    "ai.groq_client",
    "ai.engine", 
    "ai.prompts",
    "ai.lexscan_engine"
]

for module in modules_to_test:
    try:
        result = subprocess.run(
            [venv_python, "-c", f"import {module}; print('OK: {module}')"],
            cwd=os.path.join(os.path.dirname(__file__), 'backend'),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"[OK] {module}")
        else:
            print(f"[ERRO] {module}")
            print(f"   Stderr: {result.stderr[:200]}")
    except Exception as e:
        print(f"[ERRO] {module}: {e}")

# Teste 3: Verificar estrutura de arquivos IA
print("\n[3/5] Verificando estrutura de arquivos IA...")
ai_files = [
    "backend/ai/engine.py",
    "backend/ai/groq_client.py",
    "backend/ai/prompts.py",
    "backend/ai/lexscan_engine.py"
]

for file_path in ai_files:
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"[OK] {file_path} ({size} bytes)")
    else:
        print(f"[ERRO] {file_path} nao encontrado")

# Teste 4: Verificar prompts juridicos
print("\n[4/5] Verificando prompts juridicos...")
try:
    result = subprocess.run(
        [venv_python, "-c", "from ai.prompts import LEGAL_PROMPTS; print('Prompts:', len(LEGAL_PROMPTS))"],
        cwd=os.path.join(os.path.dirname(__file__), 'backend'),
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode == 0:
        print("[OK] Prompts juridicos carregados")
        print(f"   Output: {result.stdout.strip()}")
    else:
        print("[ERRO] Erro ao carregar prompts")
        print(f"   Stderr: {result.stderr}")
except Exception as e:
    print(f"[ERRO] Excecao: {e}")

# Teste 5: Teste de engine basica
print("\n[5/5] Testando inicializacao da engine...")
try:
    result = subprocess.run(
        [venv_python, "-c", "from ai.engine import NeoBusinessAI; engine = NeoBusinessAI(); print('Engine inicializada com sucesso')"],
        cwd=os.path.join(os.path.dirname(__file__), 'backend'),
        capture_output=True,
        text=True,
        timeout=15
    )
    if result.returncode == 0:
        print("[OK] Engine inicializada com sucesso")
        print(f"   Output: {result.stdout.strip()}")
    else:
        print("[ERRO] Erro ao inicializar engine")
        print(f"   Stderr: {result.stderr[:300]}")
except Exception as e:
    print(f"[ERRO] Excecao: {e}")

print("\n" + "=" * 60)
print("TESTE CONCLUIDO")
print("=" * 60)
print("\nResumo dos testes realizados:")
print("[1] Configuracao do sistema")
print("[2] Importacao de modulos IA")
print("[3] Estrutura de arquivos IA")
print("[4] Prompts juridicos")
print("[5] Inicializacao da engine")
print("\nNota: Para testes completos com chamadas reais a API,")
print("configure as credenciais (GROQ_API_KEY, OPENAI_API_KEY, etc.) no .env")
